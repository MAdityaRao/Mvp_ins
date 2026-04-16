
AI Insurance Voice Agent Platform



A production-oriented AI system that enables real-time, voice-driven interactions for insurance services using LLMs, tool calling, and a scalable PostgreSQL backend.

This project demonstrates how to move beyond simple AI demos and build a complete, low-latency system that integrates speech processing, reasoning, and structured data retrieval.


---

Demo

https://your-demo-video-link

> Real-time voice interaction with live database retrieval (~2s latency)




---

Why This Project

Most AI projects focus only on model outputs.

This project focuses on system design — integrating real-time voice, LLM reasoning, and structured databases into a single low-latency pipeline.

It demonstrates how to build AI systems that:

Operate under real-world constraints

Handle noisy human input

Retrieve and act on live data

Deliver consistent, production-like performance



---

Overview

This platform provides an intelligent conversational interface where users can interact via voice or text to:

Retrieve policy details

Check claim status

Understand insurance terms

Access premium and payment information


The system combines LLM reasoning with structured backend execution to ensure accuracy, speed, and real-world usability.


---

System Architecture

Client (Voice/Text)
        │
        ▼
Speech-to-Text (STT)
        │
        ▼
LLM Agent (Reasoning + Tool Selection)
        │
   ┌────┴───────────┐
   ▼                ▼
Database Tool     Regulation Tool
(PostgreSQL)      (Rules Engine)
   │                │
   └──────┬─────────┘
          ▼
     LLM Response
          │
          ▼
Text-to-Speech (TTS)
          │
          ▼
     Client Output


---

Core Components

AI Agent Layer

LLM-based reasoning with tool calling

Context-aware multi-turn conversations

Dynamic decision-making between tools



---

Database Layer

Production-style relational schema:

Tables:

customers

policies

claims

payments

nominees

policy_coverages

claim_status_history


Design Highlights:

Normalized schema with foreign keys

Indexed queries for low latency

Real-world insurance modeling



---

Query Optimization

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

Indexes:

CREATE INDEX idx_policy_number ON policies(policy_number);
CREATE INDEX idx_claim_policy_id ON claims(policy_id);


---

Voice Processing Pipeline

User Speech → STT → LLM → Tool Execution → LLM → TTS → Audio Output


---

Key Features

Real-time voice interaction

LLM tool-calling for backend execution

Optimized PostgreSQL queries

Context-aware multi-turn conversations

Modular and extensible architecture



---

Performance

Component	Latency

Speech-to-Text	300–500 ms
LLM Processing	700–1000 ms
Database Query	50–150 ms
Text-to-Speech	800–1300 ms
End-to-End	~2–4 seconds



---

Tech Stack

Python (async backend)

PostgreSQL (Neon cloud)

LiveKit (real-time voice orchestration)

LLM APIs (tool calling)

WebRTC



---

Setup

Prerequisites

Python 3.10+

PostgreSQL / Neon instance

API keys for LLM and voice services



---

Installation

git clone https://github.com/MAdityaRao/Mvp_ins.git
cd Mvp_ins

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt


---

Environment Variables

Create a .env file:

DATABASE_URL=your_postgres_url
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret


---

Run

uv run src/agent.py console


---

AI Tools

Tool Name	Description

search_customer	Fetch policy and claim data
get_regulation	Retrieve insurance rules



---

Production Considerations

Secure secrets using environment variables

Use connection pooling for PostgreSQL

Add logging and monitoring

Implement rate limiting

Use streaming STT/TTS for lower latency



---

Future Improvements

Sub-2s latency optimization

Multilingual voice support

Payment integration

Monitoring dashboard

Analytics layer



---

Use Cases

Insurance customer support automation

Claims inquiry systems

Policy management assistants

Voice-enabled financial services



---

Author

Aditya 
Focus: AI Systems, LLM Applications, Real-Time Architectures


---

Summary

This project demonstrates how to combine LLMs, real-time voice systems, and relational databases to build production-oriented AI applications that operate under real-world constraints.