🛠️ FixIt Buddy — EU Right-to-Repair Navigator 🇪🇺

Making repair laws actually usable.

🔗 Live Demo:
👉 https://fixit-buddy-odwb.vercel.app/?_vercel_share=59cXZlmBNtdvGqRCTIcDgPQbcAi2OeKv

🎯 Overview

The EU Right-to-Repair Directive (2023/1670) aims to make devices more repairable.

But in reality:

Legal language is hard to understand
Repair manuals are too technical
Users don’t know where to start

FixIt Buddy bridges that gap.

It translates complex regulations and repair documentation into clear, actionable, step-by-step guidance — with built-in safety checks.

⚙️ What It Does
🔍 Converts technical repair manuals into plain language
🧠 Uses AI to guide users through repair steps
⚠️ Injects safety warnings (heat, ESD, adhesives)
🧭 Falls back to trusted sources when uncertain
💶 Enforces EU pricing rules (e.g., 30% MSRP cap)
🏗️ System Architecture

Frontend: Next.js 15 (Vercel)
Backend: FastAPI (Railway)
Database: PostgreSQL 16

Performance:

⚡ <50ms latency for core APIs
🤖 2–5s response time for AI chat (Groq inference)
🧠 Key Engineering Decision
From RAG → Lightweight Inference

Initially, the system used a full RAG pipeline:

FAISS
sentence-transformers

It worked well — but the container size reached 6.5GB, exceeding Railway’s 4GB limit.

Decision:
❌ Drop RAG (too heavy for deployment)
✅ Switch to Groq-hosted Llama 3.1 8B
Outcome:
Production-ready deployment
Sub-5 second responses
Fits within infrastructure constraints

Prioritized shipping a working system over architectural perfection.

🛠️ Engineering Practices
✅ Data Validation: Pydantic models for strict API schemas
🔐 Security: CORS configuration + environment variables for secrets
🚀 CI/CD: GitHub → Vercel & Railway auto-deploy pipelines
🚦 AI Safety & Reliability
📉 Confidence Thresholding:
Redirects users to trusted sources (e.g., iFixit) when uncertain
⚠️ Safety Guardrails:
Mandatory warnings for risky steps (heat guns, adhesives, ESD)
🧾 Plain Language Mapping:
Converts technical jargon into user-friendly descriptions
🗄️ Data Strategy

Current:

Seeded in-memory mock data for high availability

Schema:

devices
spare_parts
repair_sessions

Planned:

Full database-driven queries
Expand to 20+ supported devices
🚀 Getting Started (Local Setup)
Prerequisites
Python 3.11+
Node.js 20+
Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
Frontend
cd frontend
npm install
npm run dev
🗺️ Roadmap
v1.1 → Reintroduce RAG pipeline with scalable infra
v1.2 → Integrate EU Digital Product Passport (CIRPASS API)
v1.3 → A/B test AI prompts for repair success rates
🧠 Key Learnings
Shipping > perfect architecture
Constraints drive better decisions
AI needs guardrails, not just intelligence
Real value = translation, not generation
🤝 Contributing

Contributions, ideas, and feedback are welcome.
Feel free to open issues or submit PRs.
