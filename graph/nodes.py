"""
Graph Node Implementations
===========================
Each function receives the full ChatbotState dict, performs its
work, and returns a *partial* dict with only the keys it updates.
LangGraph merges the partial update into the running state.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import get_llm, invoke_with_retry
from prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from prompts.assistant_prompt import ASSISTANT_SYSTEM_PROMPT
from tools.inventory_api import query_inventory_api
from tools.rag_knowledge_base import query_rag_faq
from graph.state import ChatbotState


# ===============================================================
#  1. ROUTER NODE
# ===============================================================

def router_node(state: ChatbotState) -> dict[str, Any]:
    """
    Classify the user's intent using an LLM call and decide
    which downstream path to take.

    Updates
    -------
    router_decision : str
        One of "inventory_api", "knowledge_base_rag", or "conversational".
    """
    llm = get_llm()

    messages = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=state["user_input"]),
    ]

    response = invoke_with_retry(llm, messages)
    raw_text = response.content.strip()

    # -- Parse the JSON from the LLM
    try:
        parsed = json.loads(raw_text)
        decision = parsed.get("next_step", "conversational")
    except json.JSONDecodeError:
        # Fallback: try to extract from malformed output
        match = re.search(
            r'"next_step"\s*:\s*"(inventory_api|knowledge_base_rag|conversational)"',
            raw_text,
        )
        decision = match.group(1) if match else "conversational"

    # Validate
    valid_routes = {"inventory_api", "knowledge_base_rag", "conversational"}
    if decision not in valid_routes:
        decision = "conversational"

    print(f"  [Router] Decision -> {decision}")
    return {"router_decision": decision}


# ===============================================================
#  2. INVENTORY API TOOL NODE
# ===============================================================

def inventory_api_node(state: ChatbotState) -> dict[str, Any]:
    """
    Call the mock ERP / inventory API and store the JSON
    result in ``retrieved_context``.

    Also calls the RAG knowledge base to enrich the context
    with static technical data (since inventory queries often
    include spec questions too).
    """
    user_input = state["user_input"]

    # -- Extract PIN code from the query if present (6 digits for India)
    pin_match = re.search(r"\b(\d{6})\b", user_input)
    pin_code = pin_match.group(1) if pin_match else None

    # -- Fetch live inventory data
    inventory_json = query_inventory_api(user_input, pin_code=pin_code)

    # -- Also pull static specs for richer answers
    rag_chunks = query_rag_faq(user_input)

    combined_context = (
        "== LIVE INVENTORY DATA ==\n"
        f"{inventory_json}\n\n"
        "== KNOWLEDGE BASE (Technical Specs / FAQs) ==\n"
        f"{rag_chunks}"
    )

    print("  [Tool] Inventory API + RAG context retrieved.")
    return {"retrieved_context": combined_context}


# ===============================================================
#  3. RAG / KNOWLEDGE-BASE TOOL NODE
# ===============================================================

def knowledge_base_rag_node(state: ChatbotState) -> dict[str, Any]:
    """
    Query the mock vector store for relevant FAQ / spec chunks
    and store them in ``retrieved_context``.
    """
    rag_chunks = query_rag_faq(state["user_input"])

    context = (
        "== KNOWLEDGE BASE (Technical Specs / FAQs) ==\n"
        f"{rag_chunks}"
    )

    print("  [Tool] Knowledge-base context retrieved.")
    return {"retrieved_context": context}


# ===============================================================
#  4. CONVERSATIONAL NODE (no tool needed)
# ===============================================================

def conversational_node(state: ChatbotState) -> dict[str, Any]:
    """
    For greetings / chit-chat: no external data needed.
    Sets a minimal context so the assistant knows this is
    a conversational exchange.
    """
    print("  [Chat] Conversational path -- no data retrieval needed.")
    return {
        "retrieved_context": (
            "This is a general conversational exchange (greeting or "
            "closing remark). No product data was retrieved. Respond "
            "warmly as a representative of Ayansh Infocom Private Limited."
        )
    }


# ===============================================================
#  5. ASSISTANT NODE -- Final response generation
# ===============================================================

def assistant_node(state: ChatbotState) -> dict[str, Any]:
    """
    Generate the final customer-facing response using the
    Core Assistant System Prompt and all retrieved context.

    Updates
    -------
    final_response : str
        The polished answer to display to the customer.
    """
    llm = get_llm()

    # -- Hydrate the prompt template
    system_prompt = ASSISTANT_SYSTEM_PROMPT.format(
        system_retrieved_context=state.get("retrieved_context", "No context available."),
        user_input=state["user_input"],
    )

    messages = [SystemMessage(content=system_prompt)]
    
    from langchain_core.messages import AIMessage
    
    # Append chat history
    for msg in state.get("chat_history", []):
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # Append current user input
    messages.append(HumanMessage(content=state["user_input"]))

    response = invoke_with_retry(llm, messages)
    answer = response.content.strip()

    print("  [Done] Assistant response generated.\n")
    return {"final_response": answer}
