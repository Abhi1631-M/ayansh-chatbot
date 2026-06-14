---
title: Ayansh Chatbot
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🌐 Ayansh Infotech Pvt. Ltd. — AI Customer Support & Sales Chatbot
> **Intelligent, graph-based chatbot** for networking hardware e-commerce — powered by **LangGraph**, **LangChain**, **FastAPI**, and **ChromaDB**.

---

## ✨ Features

| Capability | Description |
|---|---|
| 🔀 **Intent Routing** | LLM-powered router classifies queries into inventory, knowledge-base, or conversational paths |
| 📦 **Real-time Inventory** | SQLite-backed ERP API returns price, stock, tax (by ZIP), shipping dates, and promotional offers |
| 📚 **RAG Knowledge Base** | ChromaDB semantic vector-store serves product specs, manuals, FAQs, and company policies |
| 🤖 **AI Sales Assistant** | Powered by blazing-fast Groq Llama 3 models |
| 📱 **WhatsApp Integration** | Webhook ready for direct Meta WhatsApp Business API integration |
| 💻 **Web UI & Admin Portal** | Beautiful chat interface for customers and an Admin portal for viewing chat logs |

---

## 🚀 Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/Abhi1631-M/ayansh-chatbot.git
cd ayansh-chatbot
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory (you can copy `.env.example`).
You MUST configure the following secrets:

```env
# AI Model Configuration
GROQ_API_KEY=your_groq_api_key_here

# Admin Portal Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password

# WhatsApp API Configuration (Optional)
WHATSAPP_ACCESS_TOKEN=your_meta_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_VERIFY_TOKEN=your_custom_webhook_secret
```

### 3. Initialize Databases
```bash
python -m database.seed
python -m database.sync_vectors
```

### 4. Run the Server
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```
- **Chat UI:** http://localhost:8000
- **Admin Portal:** http://localhost:8000/admin

---

## ☁️ Cloud Deployment (Hugging Face Spaces)

This application is fully Dockerized and optimized to run entirely for free on Hugging Face Spaces!

1. Create a free account on [Hugging Face](https://huggingface.co).
2. Create a new Space:
   - **SDK:** Docker -> Blank
   - **Hardware:** CPU Basic (Free - 16GB RAM)
3. In your new Space, click **Settings** -> **Variables and secrets**.
4. Add all the secrets from your `.env` file (e.g., `GROQ_API_KEY`, `ADMIN_USERNAME`) as **Secrets**.
5. Connect your GitHub repository or push your code directly to the Hugging Face space. The `Dockerfile` handles everything!

---

## 🏢 Company

**Ayansh Infotech Pvt. Ltd.**  
Premier provider of networking infrastructure products.

---

## 📄 License

Proprietary — Ayansh Infotech Pvt. Ltd. All rights reserved.
