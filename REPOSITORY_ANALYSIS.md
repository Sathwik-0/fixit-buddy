# FixIt Buddy - Complete Repository Analysis

## 📋 Project Overview

**FixIt Buddy** is an AI-powered chatbot designed to help everyday people repair their electronics while navigating EU Right-to-Repair laws (Directive 2023/1670). The platform translates complex repair manuals and regulations into clear, actionable, step-by-step guidance with built-in safety checks.

### Key Objectives
- Make repair laws accessible and understandable
- Convert technical repair manuals into plain language
- Enforce EU pricing rules (30% MSRP cap for spare parts)
- Inject mandatory safety warnings
- Deploy reliably within infrastructure constraints

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FixIt Buddy                          │
│                                                         │
│  Frontend (Next.js 15)          Backend (FastAPI)       │
│  ├── React Components            ├── RAG Service        │
│  ├── Chatbot UI                  ├── Score Router       │
│  ├── Device Search               ├── Parts Router       │
│  └── Parts Pricing               ├── SQLAlchemy ORM     │
│       (Vercel)                   └── Groq Llama 3.1     │
│                                       (Railway)          │
│                                                         │
│                 PostgreSQL 16 Database                  │
│              (Supabase or Railway)                      │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, React, TypeScript | Modern UI framework with App Router |
| **UI Framework** | Tailwind CSS, Radix UI | Responsive design and accessible components |
| **Backend** | FastAPI (Python 3.11+) | Async REST API with automatic docs |
| **Database** | PostgreSQL 16 | Relational data storage, JSONB for AI results |
| **AI/LLM** | Groq (Llama 3.1 8B) | Fast, hosted inference (~2-5s responses) |
| **Storage** | Supabase Storage / Railway | File uploads for repair manuals |
| **Deployment** | Vercel (frontend), Railway (backend) | Serverless scaling |

---

## 📁 Directory Structure

```
fixit-buddy/
├── backend/                    # FastAPI application
│   ├── main.py                # Entry point, CORS setup
│   ├── requirements.txt        # Python dependencies
│   ├── railway.toml           # Railway deployment config
│   ├── routers/
│   │   ├── score.py           # Device repairability scoring
│   │   ├── rag.py             # PDF upload + RAG chat
│   │   └── parts.py           # EU 30% price compliance check
│   ├── services/
│   │   └── rag_service.py     # Groq + Llama 3.1 integration
│   ├── models/
│   │   └── database.py        # SQLAlchemy models
│   └── .env.example           # Environment template
│
├── frontend/                   # Next.js application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── page.tsx       # Home + chatbot UI
│   │   │   └── globals.css    # Tailwind imports
│   │   ├── lib/
│   │   │   └── api.ts         # Axios/fetch API wrapper
│   │   └── components/
│   │       ├── DeviceSearch.tsx
│   │       ├── ChatBot.tsx
│   │       └── PartsTable.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md        # Detailed design decisions
│   └── DEPLOYMENT.md          # Step-by-step guides
│
└── README.md                   # User-facing documentation
```

---

## 🔑 Core Components

### 1. **Backend: `/backend/main.py`**
**Purpose:** FastAPI server that coordinates AI chat, device data, and parts pricing.

**Key Features:**
- CORS-enabled for Vercel frontend
- Pydantic models for strict request/response validation
- Environment-based configuration (GEMINI_API_KEY, DATABASE_URL)
- Automatic OpenAPI docs at `/docs`

**Critical Design:** Using Groq instead of RAG to keep container size under 4GB (Railway limit).

---

### 2. **AI/RAG Service: `/backend/services/rag_service.py`**
**Purpose:** Integrates with Groq Llama 3.1 8B for LLM inference and PDF processing.

**Functionality:**
- Accepts PDF repair manuals
- Extracts text and embeds context
- Streams AI responses with confidence thresholding
- Falls back to trusted sources (iFixit) when uncertain

**Why Groq?**
- Fast inference (~2-5s vs 10-30s with other providers)
- Hosted solution = no GPU infrastructure needed
- Cost-effective for high-volume requests
- Works within Railway's deployment constraints

---

### 3. **Device & Repairability Scoring: `/backend/routers/score.py`**
**Purpose:** Tracks device repair difficulty and required documentation.

**Schema:**
```python
{
  "device_id": "fairphone-5",
  "name": "Fairphone 5",
  "repairability_score": 8.5,  # Out of 10
  "spare_parts": [
    {
      "name": "Battery",
      "eu_msrp": 79.99,
      "regulated_price_cap": 24.00  # 30% rule
    }
  ],
  "manual_url": "https://..."
}
```

---

### 4. **EU Pricing Compliance: `/backend/routers/parts.py`**
**Purpose:** Enforces EU Right-to-Repair price caps (30% of MSRP).

**Example:**
- Original MSRP: €99
- EU price cap: €29.70 (30%)
- Any seller quoting > €29.70 triggers a warning

---

### 5. **Frontend: Chatbot UI**
**Purpose:** React-based interface for users to search devices and ask repair questions.

**Screens:**
1. **Device Search** → Find your device
2. **AI Chat** → Ask repair questions with optional PDF upload
3. **Parts Pricing** → View EU-compliant part costs
4. **Safety Warnings** → Display alerts for risky steps (heat guns, ESD, adhesives)

---

## 🚀 Key Workflows

### Workflow 1: User Asks Repair Question

```
User selects device (Fairphone 5)
        ↓
Sends: "How do I replace the battery?"
        ↓
Frontend → POST /api/rag/chat
        ↓
Backend fetches device context (from mock data)
        ↓
Groq Llama processes request
        ↓
Response returned with:
  ✓ Step-by-step instructions
  ✓ Safety warnings injected
  ✓ Confidence score
  ✓ Fallback to iFixit if uncertain
        ↓
UI displays formatted response
```

### Workflow 2: Parts Pricing Compliance Check

```
User opens Parts tab for Fairphone 5
        ↓
Frontend → GET /api/parts?device=fairphone-5
        ↓
Backend calculates:
  - MSRP price (from database)
  - EU cap: 30% × MSRP
  - Market prices (if available)
        ↓
Returns compliance report:
  ✓ Part name
  ✓ EU cap price
  ✓ Recommended vendors
  ✓ Violation flags if needed
        ↓
UI renders as sortable table
```

---

## 🛠️ Engineering Decisions & Tradeoffs

### Decision: RAG → Groq Inference
**Problem:** Full RAG pipeline (FAISS + sentence-transformers) reached 6.5GB container size, exceeding Railway's 4GB limit.

**Options Considered:**
1. ❌ RAG with Pinecone (adds dependency, cost)
2. ❌ Self-hosted vector DB (operations overhead)
3. ✅ **Groq-hosted LLM (chosen)**

**Rationale:**
- Reduces complexity
- Fits deployment constraints
- Faster response times
- Simpler to debug and maintain

**Tradeoff:** Less precise recall on domain-specific content (mitigated by safety guardrails).

---

### Decision: Pydantic Validation
**Purpose:** Strict input/output schema enforcement.

**Example:**
```python
class RepairQueryRequest(BaseModel):
    device_id: str
    question: str
    manual_pdf: Optional[UploadFile] = None
    confidence_threshold: float = 0.7  # Default: redirect if < this

class RepairQueryResponse(BaseModel):
    steps: List[str]
    warnings: List[SafetyWarning]
    confidence: float
    sources: List[str]
```

**Benefit:** Catches malformed requests early, auto-generates API docs.

---

### Decision: Plain Language Mapping
**Purpose:** Translate technical jargon into user-friendly language.

**Example Mapping:**
```
Technical: "Apply thermal conductive adhesive with ESD-safe applicator"
↓
Plain: "Carefully apply heat-conductive glue using an anti-static tool"
↓
Plus Warning: ⚠️ "Watch for burns! Adhesive dries in 10 minutes."
```

---

## 🔐 Safety & Reliability

### Confidence Thresholding
- If Groq confidence < 0.7 → redirect to iFixit
- Never give uncertain guidance on safety-critical steps

### Mandatory Safety Warnings
Applied to steps involving:
- Heat (> 60°C)
- Electricity/ESD
- Toxic adhesives
- Sharp components

### EU Compliance
- Price caps automatically enforced
- Routing to compliant vendors
- Audit trail for pricing violations

---

## 📊 Data Strategy

### Current (MVP)
- In-memory mock data for high availability
- PostgreSQL for future expansion
- No external API dependencies (except Groq)

### Planned
- Full database-driven device catalog (50+ devices)
- EU Digital Product Passport (CIRPASS API) integration
- A/B testing on AI prompts for repair success rates

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Groq API key (free: console.groq.com)
- Railway or Vercel account

### Local Development (5 minutes)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GROQ_API_KEY to .env
uvicorn main:app --reload
# API running at http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local
# Add NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# App running at http://localhost:3000
```

### Deploying to Production

**Backend (Railway):**
1. Connect GitHub repo
2. Set root directory to `backend/`
3. Add `GROQ_API_KEY` environment variable
4. Railway auto-deploys on push

**Frontend (Vercel):**
1. Connect GitHub repo
2. Set root directory to `frontend/`
3. Add `NEXT_PUBLIC_API_URL=<railway-url>`
4. Vercel auto-deploys on push

---

## 📈 Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| API response time | < 5s | 2-5s (Groq inference) |
| Chat latency | < 1s | ~800ms (client-side) |
| Device lookup | < 100ms | ~50ms (mock data) |
| Parts pricing query | < 200ms | ~80ms (DB cached) |

---

## 🗺️ Roadmap

### v1.1
- Reintroduce RAG pipeline with scalable infra (Supabase pgvector)
- Add vector similarity search for better manual matching

### v1.2
- EU Digital Product Passport (CIRPASS API) integration
- Expand device catalog to 50+ devices
- Multi-language support (EU languages)

### v1.3
- A/B test AI prompts for repair success rates
- User repair history tracking
- Community repair tips integration

---

## 🧠 Key Learnings

1. **Shipping > Perfect Architecture**
   - Chose simpler Groq solution over complex RAG to ship faster
   - Better to iterate with users than spend time optimizing prematurely

2. **Constraints Drive Better Decisions**
   - 4GB Railway limit forced smarter tech choices
   - Real-world limits improve engineering rigor

3. **AI Needs Guardrails**
   - Confidence thresholding prevents dangerous advice
   - Safety warnings non-negotiable for repair guidance

4. **Real Value = Translation, Not Generation**
   - Users need jargon simplified, not new content
   - Plain language mapping is more useful than raw LLM output

---

## 🤝 Contributing

Contributions welcome! Areas for help:
- [ ] Additional device manuals
- [ ] Localization (French, German, etc.)
- [ ] Safety warning taxonomy expansion
- [ ] EU compliance research
- [ ] UX improvements

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

MIT License - See [LICENSE](LICENSE)

---

## 🔗 Resources

- [EU Right-to-Repair Directive 2023/1670](https://eur-lex.europa.eu/)
- [iFixit Repair Guides](https://ifixit.com/)
- [Groq API Docs](https://console.groq.com/docs)
- [Llama 3.1 Model Card](https://huggingface.co/meta-llama/Llama-3.1-8B)

