# 🌐 Ayansh Infotech Pvt. Ltd. — AI Customer Support & Sales Chatbot

> **Intelligent, graph-based chatbot** for networking hardware e-commerce — powered by **LangGraph**, **LangChain**, and **RAG**.

---

## ✨ Features

| Capability | Description |
|---|---|
| 🔀 **Intent Routing** | LLM-powered router classifies queries into inventory, knowledge-base, or conversational paths |
| 📦 **Real-time Inventory** | Mock ERP API returns price, stock, tax (by ZIP), shipping dates, and promotional offers |
| 📚 **RAG Knowledge Base** | Mock vector-store retriever serves product specs, manuals, FAQs, and company policies |
| 🤖 **AI Sales Assistant** | Final LLM node generates polished, context-rich customer responses |
| 🛡️ **Guardrails** | Never hallucinates data; suggests alternatives for out-of-stock items |

---

## 📁 Project Structure

```
ayansh-infotech-chatbot/
├── main.py                          # Entry point (demo + interactive mode)
├── requirements.txt                 # Python dependencies
├── .env.example                     # API key template
│
├── config/
│   └── settings.py                  # LLM factory & env config
│
├── prompts/
│   ├── router_prompt.py             # Router system prompt
│   └── assistant_prompt.py          # Core assistant system prompt
│
├── tools/
│   ├── inventory_api.py             # Mock ERP/inventory API
│   └── rag_knowledge_base.py        # Mock vector-store FAQ retriever
│
├── graph/
│   ├── state.py                     # ChatbotState TypedDict
│   ├── nodes.py                     # All graph node functions
│   ├── edges.py                     # Conditional routing logic
│   └── builder.py                   # StateGraph assembly & compilation
│
└── tests/
    └── test_chatbot.py              # Unit + integration tests
```

---

## 🏗️ Architecture

```
┌────────────┐
│  __start__ │
└─────┬──────┘
      ▼
┌────────────┐
│   Router   │  ← LLM classifies intent
└─────┬──────┘
      │  conditional edge
      ├────────────────────┬─────────────────────┐
      ▼                    ▼                     ▼
┌───────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Inventory API │ │ Knowledge Base   │ │ Conversational   │
│     Node      │ │   RAG Node       │ │     Node         │
└───────┬───────┘ └────────┬─────────┘ └────────┬─────────┘
        │                  │                     │
        └──────────────────┼─────────────────────┘
                           ▼
                  ┌────────────────┐
                  │   Assistant    │  ← LLM generates answer
                  └────────┬───────┘
                           ▼
                    ┌────────────┐
                    │   __end__  │
                    └────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd ayansh-infotech-chatbot
pip install -r requirements.txt
```

### 2. Set API Key

```bash
cp .env.example .env
# Edit .env and add your OpenAI or Google API key
```

### 3. Run Demo

```bash
python main.py
```

### 4. Interactive Chat

```bash
python main.py --interactive
```

### 5. Run Tests

```bash
python -m pytest tests/test_chatbot.py -v
```

---

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `GOOGLE_API_KEY` | — | Your Google Gemini API key (alternative) |
| `LLM_PROVIDER` | `openai` | Set to `google` to use Gemini |

Edit `config/settings.py` to change model names or temperature.

---

## 📦 Mock Product Catalogue

The demo includes 5 realistic products:

| Product | ID | Price | Stock |
|---|---|---|---|
| ProMount 42U Server Rack | SR-42U-PRO | $1,249.99 | ✅ 14 units |
| ShieldLink 24-Port CAT6A Patch Panel | PP-24-CAT6A | $89.99 | ✅ 230 units |
| AirStream AX6000 Wi-Fi 6E Router | WR-AX6000-E | $549.99 | ✅ 42 units |
| ChannelPath 300mm Cable Tray | CT-300-HDG | $64.50 | ❌ Out of stock |
| NetForce 48-Port PoE+ Switch | SW-48P-GBE | $899.00 | ✅ 18 units |

---

## 🏢 Company

**Ayansh Infotech Pvt. Ltd.**  
Premier provider of networking infrastructure products.

---

## 📄 License

Proprietary — Ayansh Infotech Pvt. Ltd. All rights reserved.
