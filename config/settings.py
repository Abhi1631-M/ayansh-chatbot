"""
Ayansh Infotech Pvt. Ltd. -- Configuration & LLM Factory
=========================================================
Uses Groq free tier (Llama 3 models) by default.
Free: 30 requests/min, 15,000 tokens/min — no credit card.

Get your FREE API key:
  https://console.groq.com/keys
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

# -- Load .env from project root
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

# -- Constants
COMPANY_NAME: str = "Ayansh Infocom Private Limited"
LLM_TEMPERATURE: float = 0.1
LLM_MODEL: str = "llama-3.3-70b-versatile"   # Groq free: fast, high quality


def get_llm():
    """Return a Groq ChatModel instance."""
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key == "your-groq-api-key-here":
        raise ValueError(
            "\n\n"
            "+==============================================================+\n"
            "|  GROQ_API_KEY not set!                                       |\n"
            "|                                                              |\n"
            "|  1. Go to https://console.groq.com/keys                     |\n"
            "|  2. Sign up (FREE, no credit card needed)                    |\n"
            "|  3. Click 'Create API Key' and copy it                       |\n"
            "|  4. Paste your key in the .env file                          |\n"
            "+==============================================================+\n"
        )

    return ChatGroq(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        groq_api_key=api_key,
    )


def invoke_with_retry(llm, messages, max_retries: int = 3):
    """
    Invoke the LLM with automatic retry + exponential backoff
    for rate-limit (429) errors.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return llm.invoke(messages)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                wait_time = 15 * attempt   # 15s, 30s, 45s
                print(f"  [Rate Limit] Waiting {wait_time}s before retry "
                      f"({attempt}/{max_retries})...")
                time.sleep(wait_time)
                if attempt == max_retries:
                    raise
            else:
                raise
