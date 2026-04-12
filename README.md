# 🏦 AI Insurance Voice Agent Platform

A production-ready **AI-powered insurance assistant** that enables real-time, voice-driven customer interactions for policy management, claims tracking, and support.

Built using modern AI systems, real-time communication infrastructure, and a scalable PostgreSQL backend, this platform demonstrates how conversational AI can be integrated into financial and insurance workflows.

---

## 📖 Overview

This system provides an **intelligent conversational interface** for insurance services. Users can interact via voice or text to:

* Retrieve policy details
* Check claim status
* Understand insurance terms (e.g., lapsed policy)
* Get premium and payment information

The system leverages **LLM-based reasoning with structured tool execution**, ensuring both accuracy and low latency.

---

## 🧱 Architecture

```text
Client (Voice/Text)
        │
        ▼
Speech-to-Text (STT)
        │
        ▼
LLM Agent (Reasoning + Tool Selection)
        │
        ├──► Database Tool (PostgreSQL - Neon)
        │
        └──► Knowledge Tool (Regulations / Rules)
        │
        ▼
Text-to-Speech (TTS)
        │
        ▼
Client Response
```

---

## ⚙️ Core Components

### 1. 🤖 AI Agent Layer

* Handles **intent detection and response generation**
* Uses **tool-calling architecture**
* Supports **context-aware conversations**

---

### 2. 🗄️ Database Layer

A normalized PostgreSQL schema designed for real-world insurance systems.

#### Key Tables:

* `customers`
* `policies`
* `claims`
* `payments`
* `nominees`
* `policy_coverages`
* `claim_status_history`

#### Design Principles:

* Referential integrity via foreign keys
* Indexed query paths for low latency
* Realistic relational modeling

---

### 3. 🔍 Query Optimization

Example optimized query for policy lookup:

```sql
SELECT
    c.id AS customer_id,
    c.full_name,
    c.phone,
    p.id AS policy_id,
    p.policy_number,
    p.policy_type,
    p.status,
    p.premium_amount,
    p.premium_frequency,
    p.sum_insured,
    cl.claim_number,
    cl.status AS claim_status
FROM policies p
JOIN customers c ON c.id = p.customer_id
LEFT JOIN claims cl ON cl.policy_id = p.id
WHERE p.policy_number = $1;
```

#### Indexing Strategy:

```sql
CREATE INDEX idx_policy_number ON policies(policy_number);
CREATE INDEX idx_claim_policy_id ON claims(policy_id);
```

---

### 4. 🎤 Voice Processing Pipeline

```text
User Speech → STT → LLM → Tool Execution → LLM → TTS → Audio Output
```

---

## 🚀 Key Features

* Real-time **voice-based interaction**
* Structured **tool-based LLM execution**
* Optimized **database querying**
* Context-aware multi-turn conversations
* Modular and extensible architecture

---

## 📊 Performance

| Layer          | Latency (Approx) |
| -------------- | ---------------- |
| Speech-to-Text | 300–500 ms       |
| LLM Processing | 700–1000 ms      |
| Database Query | 50–150 ms        |
| Text-to-Speech | 800–1300 ms      |
| **End-to-End** | **2–4 seconds**  |

---

## 🛠️ Setup & Installation

### Prerequisites

* Python 3.10+
* PostgreSQL (or Neon cloud instance)
* API keys for voice/AI services

---

### Installation

```bash
git clone https://github.com/your-repo/insurance-ai-agent.git
cd insurance-ai-agent

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

### Environment Configuration

Create a `.env` file:

```env
DATABASE_URL=your_neon_postgres_connection_string
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
```

---

### Run the Application

```bash
uv run src/agent.py console
```

---

## 🧠 AI Tools

| Tool Name         | Description                           |
| ----------------- | ------------------------------------- |
| `search_customer` | Fetch policy & claim details          |
| `get_regulation`  | Retrieve insurance rules/explanations |

---

## 🔐 Production Considerations

* Secure database credentials using environment variables
* Enable connection pooling for PostgreSQL
* Implement request rate limiting
* Add logging and monitoring
* Use streaming STT/TTS for lower latency

---

## 📈 Future Enhancements

* Sub-2 second response latency
* Payment gateway integration
* Web dashboard for agents/customers
* Advanced analytics & reporting
* Multi-language voice support

---

## 🧪 Use Cases

* Insurance customer support automation
* Policy management assistants
* Claims inquiry systems
* Voice-enabled financial services

---

## 👨‍💻 Author

Aditya
Focus: AI Systems, Databases, and Real-Time Applications

---

## 📄 License

This project is intended for academic and demonstration purposes. Extend with appropriate licensing for production use.

---

## ⭐ Summary

This platform demonstrates how **AI agents, real-time voice systems, and relational databases** can be combined to build scalable, production-ready solutions for the insurance industry.

---
