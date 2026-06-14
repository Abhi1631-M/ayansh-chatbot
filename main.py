#!/usr/bin/env python3
"""
Ayansh Infocom Private Limited
AI Customer Support & Sales Chatbot
Powered by LangGraph - LangChain - RAG

Usage
-----
    python main.py                   # run built-in demo queries
    python main.py --interactive     # interactive chat loop

Set your API key in a `.env` file (see .env.example).
"""

from __future__ import annotations

import sys
import io

# ── Force UTF-8 output on Windows ────────────────────
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from graph.builder import chatbot_graph


def _banner() -> None:
    print("""
+==============================================================+
|   Ayansh Infocom Private Limited -- AI Sales Chatbot        |
|   Networking Hardware | Routers | Racks | Panels             |
+==============================================================+
""")


def run_query(query: str) -> str:
    """
    Execute a single user query through the chatbot graph.

    Parameters
    ----------
    query : str
        The customer's natural-language message.

    Returns
    -------
    str
        The assistant's final response.
    """
    print("-" * 64)
    print(f"  [Customer]: {query}")
    print("-" * 64 + "\n")

    result = chatbot_graph.invoke({
        "user_input": query,
        "retrieved_context": "",
        "router_decision": "",
        "final_response": "",
    })

    response = result.get("final_response", "[!] No response generated.")

    print(f"  [Ayansh Bot]:")
    print(f"  {response}\n")
    return response


def interactive_mode() -> None:
    """Run an interactive chat loop in the terminal."""
    _banner()
    print("  Type your question below. Enter 'quit' or 'exit' to leave.\n")

    while True:
        try:
            user_input = input("  You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye! Thank you for choosing Ayansh Infocom.\n")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "bye", "q"}:
            print("\n  Goodbye! Thank you for choosing Ayansh Infocom.\n")
            break

        run_query(user_input)


# ===============================================================
#  DEMO / TEST EXECUTION
# ===============================================================

def run_demo() -> None:
    """
    Run a set of diverse demo queries that exercise every
    path in the graph: inventory, RAG, conversational, and
    a complex multi-part query.
    """
    _banner()
    print("  Running demo queries ...\n")

    demo_queries = [
        # -- 1. Greeting (conversational path)
        "Hi there! I'm looking for networking equipment for my new office.",

        # -- 2. Complex multi-part query (inventory + RAG)
        (
            "Hi, do you have the 42U server rack in stock? "
            "What's the total price with tax shipping to PIN 110001, "
            "and when can it arrive? Also, what is the weight capacity?"
        ),

        # -- 3. Pure technical FAQ (RAG path)
        "What are the dimensions of the 15U wall rack and what is its load capacity?",

        # -- 4. Product inquiry with offer (inventory path)
        "I need to buy a FortiGate 40F firewall. What's the unit price and delivery date?",

        # -- 5. Out-of-stock scenario (inventory path)
        "Do you have Aruba 1930 switches in stock? I need 2 of them.",

        # -- 6. Policy question (RAG path)
        "What is your return policy and warranty coverage for Mikrotik routers?",
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'=' * 64}")
        print(f"  DEMO QUERY {i} of {len(demo_queries)}")
        print(f"{'=' * 64}")
        run_query(query)


# ===============================================================
#  ENTRY POINT
# ===============================================================

if __name__ == "__main__":
    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive_mode()
    else:
        run_demo()
