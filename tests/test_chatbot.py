"""
Unit Tests for Ayansh Infocom Chatbot
========================================
Tests the mock tools and graph routing logic *without* requiring
an LLM API key (the LLM-dependent nodes are tested only if
GROQ_API_KEY is set).

Run:  python -m pytest tests/test_chatbot.py -v
"""

from __future__ import annotations

import json
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── Tool tests (no LLM required) ────────────────────────
from tools.inventory_api import query_inventory_api
from tools.rag_knowledge_base import query_rag_faq
from graph.edges import route_after_router


# ═══════════════════════════════════════════════════════════
#  Inventory API Tests
# ═══════════════════════════════════════════════════════════

class TestInventoryAPI:
    """Tests for the mock inventory API tool."""

    def test_product_found_with_tax(self):
        """42U rack should be found; tax computed for Indian PIN."""
        result = json.loads(
            query_inventory_api("42U server rack", pin_code="110001")
        )
        assert result["status"] == "found"
        assert result["product"]["product_id"] == "SR-42U-600X1000"
        assert "tax_amount_inr" in result["pricing"]
        assert result["pricing"]["tax_region"] == "India (GST 18%)"

    def test_product_found_without_pin(self):
        """Without PIN, tax_note should appear instead of tax_amount."""
        result = json.loads(query_inventory_api("fortigate firewall"))
        assert result["status"] == "found"
        assert "tax_note" in result["pricing"]

    def test_product_not_found(self):
        """Unknown product should return not_found status."""
        result = json.loads(query_inventory_api("quantum teleporter"))
        assert result["status"] == "not_found"

    def test_out_of_stock_shows_alternative(self):
        """Fortigate is out-of-stock."""
        result = json.loads(query_inventory_api("fortigate"))
        assert result["status"] == "found"
        assert result["shipping"]["in_stock"] is False

    def test_active_offer_present(self):
        """42U rack should have an active promotional offer."""
        result = json.loads(query_inventory_api("server rack"))
        assert result["active_offer"] is not None
        assert result["active_offer"]["code"] == "RACK26K"

    def test_no_offer_for_mikrotik(self):
        """Mikrotik should have no active offer."""
        result = json.loads(query_inventory_api("mikrotik"))
        assert result["active_offer"] is None

    def test_stock_quantity_positive(self):
        """Aruba Switch should have positive stock."""
        result = json.loads(query_inventory_api("aruba"))
        assert result["shipping"]["stock_qty"] > 0

    def test_shipping_dates_present_when_in_stock(self):
        """In-stock product should have shipping date estimates."""
        result = json.loads(query_inventory_api("mikrotik routerboard"))
        assert "standard_shipping" in result["shipping"]
        assert "express_shipping" in result["shipping"]


# ═══════════════════════════════════════════════════════════
#  RAG Knowledge Base Tests
# ═══════════════════════════════════════════════════════════

class TestRAGKnowledgeBase:
    """Tests for the mock RAG FAQ retriever."""

    def test_server_rack_specs_retrieved(self):
        """Query about 42U rack should return dimension data."""
        result = query_rag_faq("What are the dimensions of the 42U server rack?")
        assert "600 mm" in result
        assert "2055 mm" in result

    def test_weight_capacity_in_result(self):
        """Load capacity question should return load specs."""
        result = query_rag_faq("load capacity of the server rack")
        assert "800 kg" in result

    def test_return_policy_retrieved(self):
        """Return policy query should hit the FAQ chunks."""
        result = query_rag_faq("What is your return policy?")
        assert "30-day" in result

    def test_warranty_info_retrieved(self):
        """Warranty query should return warranty details."""
        result = query_rag_faq("warranty for networking switches")
        assert "warranty" in result.lower()


    def test_fortigate_specs_retrieved(self):
        """Fortigate query should return specs."""
        result = query_rag_faq("FortiGate specifications")
        assert "Firewall Throughput" in result


# ═══════════════════════════════════════════════════════════
#  Conditional Edge Tests
# ═══════════════════════════════════════════════════════════

class TestConditionalEdges:
    """Tests for the routing logic."""

    def test_route_inventory(self):
        state = {
            "user_input": "",
            "retrieved_context": "",
            "router_decision": "inventory_api",
            "final_response": "",
        }
        assert route_after_router(state) == "inventory_api_node"

    def test_route_rag(self):
        state = {
            "user_input": "",
            "retrieved_context": "",
            "router_decision": "knowledge_base_rag",
            "final_response": "",
        }
        assert route_after_router(state) == "knowledge_base_rag_node"

    def test_route_conversational(self):
        state = {
            "user_input": "",
            "retrieved_context": "",
            "router_decision": "conversational",
            "final_response": "",
        }
        assert route_after_router(state) == "conversational_node"

    def test_route_unknown_defaults_conversational(self):
        state = {
            "user_input": "",
            "retrieved_context": "",
            "router_decision": "garbage_value",
            "final_response": "",
        }
        assert route_after_router(state) == "conversational_node"


# ═══════════════════════════════════════════════════════════
#  Integration Tests (require LLM API key)
# ═══════════════════════════════════════════════════════════

@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipping integration tests.",
)
class TestGraphIntegration:
    """End-to-end tests that invoke the compiled graph."""

    def test_full_graph_complex_query(self):
        from graph.builder import chatbot_graph

        result = chatbot_graph.invoke({
            "user_input": (
                "Do you have the 42U server rack in stock? "
                "What's the total price with tax for PIN 110001?"
            ),
            "retrieved_context": "",
            "router_decision": "",
            "final_response": "",
        })
        assert result["final_response"]  # non-empty
        assert result["router_decision"] in {
            "inventory_api", "knowledge_base_rag", "conversational"
        }

    def test_greeting_goes_conversational(self):
        from graph.builder import chatbot_graph

        result = chatbot_graph.invoke({
            "user_input": "Hello!",
            "retrieved_context": "",
            "router_decision": "",
            "final_response": "",
        })
        assert result["router_decision"] == "conversational"

    def test_llm_evaluation_metrics(self):
        """Use the Quality Assurance Evaluator to grade the chatbot's response."""
        from graph.builder import chatbot_graph
        from tests.evaluator import evaluate_interaction

        query = "Do you have the FortiGate 40F in stock and what's the total cost with 18% tax?"
        result = chatbot_graph.invoke({
            "user_input": query,
            "retrieved_context": "",
            "router_decision": "",
            "final_response": "",
        })

        eval_results = evaluate_interaction(
            user_input=query,
            retrieved_context=result.get("retrieved_context", ""),
            bot_output=result.get("final_response", "")
        )

        assert eval_results.get("faithfulness_score") == 1, f"Faithfulness failed: {eval_results.get('reasoning')}"
        assert eval_results.get("math_score") == 1, f"Math failed: {eval_results.get('reasoning')}"
        assert eval_results.get("routing_score") == 1, f"Routing failed: {eval_results.get('reasoning')}"
        assert eval_results.get("business_logic_score") == 1, f"Business logic failed: {eval_results.get('reasoning')}"
