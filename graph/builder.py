"""
Graph Builder & Compilation
============================
Assembles the full LangGraph StateGraph, wires all nodes and
edges, and exposes a compiled ``chatbot_graph`` ready to invoke.

Graph Topology
--------------
    ┌────────────┐
    │  __start__ │
    └─────┬──────┘
          ▼
    ┌────────────┐
    │   Router   │  ← LLM classifies intent
    └─────┬──────┘
          │  conditional edge
          ├──────────────────────┬─────────────────────┐
          ▼                      ▼                     ▼
  ┌───────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │ Inventory API │   │ Knowledge Base   │   │ Conversational   │
  │     Node      │   │   RAG Node       │   │     Node         │
  └───────┬───────┘   └────────┬─────────┘   └────────┬─────────┘
          │                    │                       │
          └────────────────────┼───────────────────────┘
                               ▼
                      ┌────────────────┐
                      │   Assistant    │  ← LLM generates answer
                      └────────┬───────┘
                               ▼
                        ┌────────────┐
                        │  __end__   │
                        └────────────┘
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from graph.state import ChatbotState
from graph.nodes import (
    router_node,
    inventory_api_node,
    knowledge_base_rag_node,
    conversational_node,
    assistant_node,
)
from graph.edges import route_after_router


def build_graph() -> StateGraph:
    """
    Construct and return the *uncompiled* StateGraph.

    Call ``.compile()`` on the returned object to get a
    runnable graph.
    """
    graph = StateGraph(ChatbotState)

    # ── Register nodes ──────────────────────────────────
    graph.add_node("router_node",            router_node)
    graph.add_node("inventory_api_node",     inventory_api_node)
    graph.add_node("knowledge_base_rag_node", knowledge_base_rag_node)
    graph.add_node("conversational_node",    conversational_node)
    graph.add_node("assistant_node",         assistant_node)

    # ── Entry point ─────────────────────────────────────
    graph.set_entry_point("router_node")

    # ── Conditional edges from router ───────────────────
    graph.add_conditional_edges(
        source="router_node",
        path=route_after_router,
        path_map={
            "inventory_api_node":       "inventory_api_node",
            "knowledge_base_rag_node":  "knowledge_base_rag_node",
            "conversational_node":      "conversational_node",
        },
    )

    # ── All tool nodes converge → assistant ─────────────
    graph.add_edge("inventory_api_node",      "assistant_node")
    graph.add_edge("knowledge_base_rag_node", "assistant_node")
    graph.add_edge("conversational_node",     "assistant_node")

    # ── Assistant → END ─────────────────────────────────
    graph.add_edge("assistant_node", END)

    return graph


def compile_graph():
    """Build and compile the chatbot graph, ready to .invoke()."""
    return build_graph().compile()


# ── Module-level compiled graph (import-friendly) ────────
chatbot_graph = compile_graph()
