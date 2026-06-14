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
> **Intelligent, graph-based chatbot** for networking hardware e-commerce — powered by **LangGraph**, **LangChain**, **FastAPI**, **Supabase (PostgreSQL)**, and **ChromaDB**.

---

## ✨ Features

| Capability | Description |
|---|---|
| 🔀 **Intent Routing** | LLM-powered router classifies queries into inventory, knowledge-base, or conversational paths |
| 📦 **Real-time Inventory** | PostgreSQL-backed ERP API returns price, stock, tax (by ZIP), shipping dates, and promotional offers |
| 📚 **RAG Knowledge Base** | ChromaDB semantic vector-store serves product specs, manuals, FAQs, and company policies |
| 🤖 **AI Sales Assistant** | Powered by blazing-fast Groq Llama 3 models |
| 🎯 **Automated Lead Generation** | AI naturally captures customer contact info & product interest during chat and saves it to a secure database |
| 📱 **WhatsApp Integration** | Connect to Twilio to reply to customers directly on WhatsApp with persistent chat memory |
| 💻 **Web UI & Admin Portal** | Beautiful chat interface for customers and an Admin portal for adding products, viewing chat logs, and tracking leads |

---

## 🚀 Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/Abhi1631-M/ayansh-chatbot.git
cd ayansh-chatbot
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory. You MUST configure the following secrets:

```env
# AI Model Configuration
GROQ_API_KEY=your_groq_api_key_here

# Supabase PostgreSQL Database (Use the Pooler URI for cloud compatibility!)
DATABASE_URL=postgresql://postgres.xxx:password@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres

# Admin Portal Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
```

### 3. Initialize Databases
The database is hosted on Supabase. Run the seed script **ONCE locally** to populate it with the default products, tables, and knowledge base chunks.
```bash
python -m database.seed
```

### 4. Run the Server
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```
- **Chat UI:** http://localhost:8000
- **Admin Portal:** http://localhost:8000/admin

---

## ☁️ Cloud Deployment (Hugging Face Spaces)

This application is fully Dockerized and optimized to run entirely for free on Hugging Face Spaces with a persistent Supabase database!

1. Create a free account on [Hugging Face](https://huggingface.co).
2. Create a new Space:
   - **SDK:** Docker -> Blank
   - **Hardware:** CPU Basic (Free - 16GB RAM)
3. In your new Space, click **Settings** -> **Variables and secrets**.
4. Add all the secrets from your `.env` file (e.g., `GROQ_API_KEY`, `ADMIN_USERNAME`, `DATABASE_URL`) as **Secrets**.
   > **Note:** Make sure you use your Supabase **Pooler** connection string for `DATABASE_URL` so that Hugging Face can connect correctly (IPv4 vs IPv6).
5. Connect your GitHub repository or push your code directly to the Hugging Face space. The `Dockerfile` handles everything!

---

## 🏢 Company

**Ayansh Infotech Pvt. Ltd.**  
Premier provider of networking infrastructure products.

---

## 📄 License

Proprietary — Ayansh Infotech Pvt. Ltd. All rights reserved.
