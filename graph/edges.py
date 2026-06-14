"""
Conditional Edge Logic
======================
Defines the routing function used by LangGraph's
``add_conditional_edges`` to pick the next node after the
Router Node.
"""

from __future__ import annotations

from graph.state import ChatbotState


def route_after_router(state: ChatbotState) -> str:
    """
    Read the router's decision from state and return the
    name of the next node to execute.

    Returns
    -------
    str
        One of the node names registered in the graph:
        ``"inventory_api_node"`` | ``"knowledge_base_rag_node"``
        | ``"conversational_node"``.
    """
    decision = state.get("router_decision", "conversational")

    routing_table = {
        "inventory_api":      "inventory_api_node",
        "knowledge_base_rag": "knowledge_base_rag_node",
        "conversational":     "conversational_node",
    }

    next_node = routing_table.get(decision, "conversational_node")
    return next_node
