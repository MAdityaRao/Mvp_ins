# AI Insurance Voice Agent Platform

A production-oriented real-time AI system that enables **voice and text-based insurance interactions** using LLMs, tool-calling, speech processing, and a structured PostgreSQL backend.

This project demonstrates how to design and build **real-world AI systems that operate under latency, structure, and reliability constraints**.

---

## 🎯 Problem Statement

Traditional insurance systems are:
- Slow (manual lookup processes)
- Non-interactive (form-based UX)
- Hard to scale in customer support

This system solves it by enabling:
> Real-time conversational access to insurance data using AI agents.

---

## ⚙️ System Architecture

User (Voice/Text Input)  
        │  
        ▼  
Speech-to-Text (STT)  
        │  
        ▼  
LLM Agent (Reasoning + Tool Selection)  
        │  
   ┌────┴────────────┐  
   ▼                 ▼  
PostgreSQL DB     Rules Engine  
(structured data)  (business logic)  
   └────┬────────────┘  
        ▼  
LLM Response Generator  
        │  
        ▼  
Text-to-Speech (TTS)  
        │  
        ▼  
User Output  

---

## 🧠 Core System Design

### 1. LLM Agent Layer
- Handles multi-turn conversation state
- Performs tool selection (function calling)
- Combines retrieved data with reasoning
- Ensures structured responses for insurance queries

---

### 2. Tool Execution Layer
The system supports controlled execution via tools such as:
- Customer lookup
- Policy retrieval
- Claim status tracking
- Regulation / rule validation

This ensures:
> LLM does not hallucinate critical insurance data

---

### 3. Database Layer (PostgreSQL)

Relational schema designed for real-world insurance workflows.

#### Core Tables:
- customers
- policies
- claims
- payments
- nominees
- policy_coverages
- claim_status_history

#### Design Principles:
- Fully normalized schema
- Foreign key relationships
- Indexed queries for low-latency access
- Optimized for read-heavy workloads

---

## ⚡ Query Optimization Example

```sql
SELECT 
    c.id AS customer_id,
    c.full_name,
    p.policy_number,
    p.policy_type,
    p.status,
    cl.claim_number,
    cl.status AS claim_status
FROM policies p
JOIN customers c ON c.id = p.customer_id
LEFT JOIN claims cl ON cl.policy_id = p.id
WHERE p.policy_number = $1;
CREATE INDEX idx_policy_number ON policies(policy_number);
CREATE INDEX idx_claim_policy_id ON claims(policy_id);
```

🎙 Voice Processing Pipeline
The system uses a streaming-based pipeline:
User Speech
→ Speech-to-Text (STT)
→ LLM Reasoning + Tool Selection
→ Database / Rules Execution
→ Response Synthesis
→ Text-to-Speech (TTS)
→ Audio Output

🧩 Key Features
Real-time voice + text interaction
LLM tool-calling architecture (no free-form hallucination for structured data)
PostgreSQL-backed deterministic retrieval
Multi-turn context-aware conversations
Modular, extensible system design

📊 Performance Profile
Component	Latency (Approx.)
Speech-to-Text	300–500 ms
LLM Processing	700–1000 ms
Database Query	50–150 ms
Text-to-Speech	800–1300 ms
Total End-to-End	~2–4 sec

🛠 Tech Stack
Python (Async backend)
PostgreSQL (Neon / cloud DB)
LLM APIs (tool calling)
LiveKit (real-time voice orchestration)
WebSockets / WebRTC
Text-to-Speech + Speech-to-Text APIs

🔐 Production Considerations
Environment-based secret management (.env)
Connection pooling for PostgreSQL
Stateless backend design for scalability
Logging layer for debugging agent decisions
Rate limiting for API safety
Streaming STT/TTS for future latency reduction

🚀 Future Improvements
Reduce end-to-end latency below 2 seconds
Add multilingual voice support
Introduce caching layer for frequent queries
Add monitoring dashboard (latency + usage metrics)
Expand tool ecosystem (payments, claims automation)
Improve retrieval accuracy via hybrid search

🎯 Real-World Use Cases
Insurance customer support automation
Policy information assistant
Claims tracking system
Voice-based financial advisory interface

👤 Author
Aditya Rao
AI Systems Engineer | LLM Applications | Real-Time Architectures
Built as a production-style AI system focused on real-world constraints: latency, reliability, and structured reasoning.    
