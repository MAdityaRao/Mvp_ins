# 🛡️ Insurance Voice AI Agent

A real-time AI-powered insurance assistant built using LiveKit, OpenAI, and PostgreSQL.
This agent can handle live voice calls, fetch customer policy data, and answer insurance-related queries using intelligent tool-calling.

---

## 🚀 Features

* 🎙️ Real-time voice interaction (STT + TTS)
* 🤖 AI-powered assistant using LLM
* 🔍 Fetch customer policy details via database
* 📜 Insurance regulations via tool-based retrieval
* ⚡ Low-latency and low-token architecture
* 🧠 Smart tool-calling (no hardcoded logic)
* 🔐 Secure environment-based configuration

---

## 🏗️ Project Structure

```
.
├── src/
│   ├── agent.py        # Main AI agent (conversation + tools)
│   ├── search.py       # Database + tools (search + regulations)
│
├── .env                # Environment variables
├── requirements.txt
├── README.md
```

---

## ⚙️ Tech Stack

* **Backend:** Python (asyncio)
* **AI/LLM:** OpenAI (GPT-4o-mini)
* **Voice:** LiveKit (STT + TTS)
* **Database:** PostgreSQL (asyncpg)
* **Validation:** Pydantic

---

## 🧠 Architecture

```
User (Voice)
   ↓
LiveKit (STT)
   ↓
Agent (LLM Brain)
   ↓
Tool Calling
   ├── search_customer → PostgreSQL
   └── get_regulation → Rule Engine
   ↓
Response
   ↓
LiveKit (TTS)
   ↓
User (Voice)
```

---

## 🗄️ Database Schema

### Customers

* id (PK)
* full_name
* phone
* email

### Policies

* id (PK)
* customer_id (FK)
* policy_number
* policy_type
* status
* premium_amount
* premium_frequency
* sum_insured

### Claims

* id (PK)
* policy_id (FK)
* claim_number
* status
* claimed_amount
* approved_amount

---

## 🔧 Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

---

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

---

### 3. Install Dependencies

```bash
uv init
pip install -r requirements.txt
```

---

### 4. Setup Environment Variables

Create `.env` file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=insurance_mvp
DB_USER=your_user
DB_PASS=your_password
```

---

### 5. Run the Agent

```bash
uv run src/agent.py start
```

---

## 🧪 Example Usage

### User:

> "My policy number is POL-2024-020"

### Agent:

* Calls `search_customer`
* Fetches data from DB
* Responds with:

  * Policy status
  * Premium details
  * Claim status

---

### User:

> "Why was my claim rejected?"

### Agent:

* Calls `get_regulation("claim")`
* Responds with rule-based explanation

---

## 🔥 Key Design Decisions

### ✅ Tool-Based Architecture

* Reduces token usage
* Improves scalability
* Separates logic cleanly

### ✅ Context7 Style Prompting

* Minimal instructions
* Behavior driven by tools

### ✅ Structured Output (Pydantic)

* Clean, predictable responses
* Easy integration with frontend

---

## ⚠️ Known Issues

* Requires active PostgreSQL instance
* Voice input may fail if microphone is not configured
* Policy number must match database format

---

## 🚀 Future Improvements

* 🎯 Automatic policy number extraction from speech
* 📊 Analytics dashboard integration
* 🧠 RAG-based regulation retrieval
* 📱 Web/mobile UI

---

## 👨‍💻 Author

Aditya

---

## 📄 License

This project is for educational and hackathon purposes.
