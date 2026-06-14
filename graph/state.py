"""
Chatbot State Definition
========================
Defines the schema for the LangGraph state. All nodes in
the graph read from and write to this dictionary.
"""

from typing import TypedDict


class ChatbotState(TypedDict):
    """
    State shared across all nodes in the AI graph.
    
    Fields
    ------
    user_input : str
        The natural language input from the user for the current turn.
        
    chat_history : list[dict]
        The conversation history, formatted as [{"role": "user", "content": "..."}, ...].

    router_decision : str
        The router's decision ("inventory_api", "knowledge_base_rag", etc.)
        
    retrieved_context : str
        A dump of data retrieved by the chosen tool.
        
    final_response : str
        The polished, customer-facing answer produced by the Assistant Node.
    """

    user_input: str
    chat_history: list[dict]
    router_decision: str
    retrieved_context: str
    final_response: str
