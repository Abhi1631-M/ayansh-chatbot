"""
Graph State Definition
======================
Defines the TypedDict that flows through every node in the
LangGraph StateGraph.
"""

from __future__ import annotations

from typing import TypedDict


class ChatbotState(TypedDict):
    """
    Shared state carried across all nodes in the graph.

    Attributes
    ----------
    user_input : str
        The raw question / message from the customer.

    retrieved_context : str
        Aggregated context returned by tool nodes (inventory JSON
        and/or RAG text chunks). Starts empty and is populated by
        the tool nodes before the assistant sees it.

    router_decision : str
        The routing label produced by the Router Node.
        One of: "inventory_api" | "knowledge_base_rag" | "conversational".

    final_response : str
        The polished, customer-facing answer produced by the
        Assistant Node.
    """

    user_input: str
    retrieved_context: str
    router_decision: str
    final_response: str
