# 🔧 FixIt Buddy — EU Right-to-Repair Navigator

An AI-powered chatbot that helps everyday people repair their electronics using EU Right-to-Repair laws.

---

## What's Inside

```
fixit-buddy/
├── backend/          ← FastAPI (Python) — deploy to Railway
│   ├── main.py
│   ├── requirements.txt
│   ├── railway.toml
│   ├── routers/
│   │   ├── score.py     ← Repairability score lookup
│   │   ├── rag.py       ← PDF upload + AI chat
│   │   └── parts.py     ← EU 30% price checker
│   ├── services/
│   │   └── rag_service.py  ← Gemini RAG pipeline
│   └── models/
│       └── database.py     ← SQLAlchemy models
└── frontend/         ← Next.js (React) — deploy to Vercel
    ├── src/app/
    │   ├── page.tsx     ← Main chatbot UI
    │   └── globals.css
    └── src/lib/
        └── api.ts       ← All API calls
```

---

## STEP 1 — Get Your Gemini API Key (Free)

1. Go to https://aistudio.google.com/app/apikey
2. Click **"Create API Key"**
3. Copy the key — you'll need it in Step 3
4. That's it! The free tier is enough to run this app

---

## STEP 2 — Put the Code on GitHub

1. Go to https://github.com and sign in
2. Click the **"+"** button → **"New repository"**
3. Name it `fixit-buddy`, set it to **Public**, click **Create**
4. Open a terminal on your computer and run:

```bash
# Navigate to the project folder
cd fixit-buddy

# Initialize git
git init
git add .
git commit -m "Initial commit — FixIt Buddy MVP"

# Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/fixit-buddy.git
git branch -M main
git push -u origin main
```

---

## STEP 3 — Deploy the Backend to Railway

Railway hosts your FastAPI backend + database for free.

1. Go to https://railway.app and sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `fixit-buddy` repo
4. Railway will ask which folder — type `backend`
5. Click **"Add Variables"** and add these:
   ```
   GEMINI_API_KEY = (paste your key from Step 1)
   ```
6. Railway will automatically detect `railway.toml` and deploy
7. Once deployed, click your service → **Settings** → copy the **Public URL**
   - It looks like: `https://fixit-buddy-production.up.railway.app`
8. **Add a database:** Click **"New"** → **"Database"** → **"PostgreSQL"**
   - Railway automatically sets `DATABASE_URL` for you ✅

---

## STEP 4 — Deploy the Frontend to Vercel

1. Go to https://vercel.com and sign up with GitHub
2. Click **"Add New Project"**
3. Import your `fixit-buddy` repo
4. Set **Root Directory** to `frontend`
5. Under **Environment Variables**, add:
   ```
   NEXT_PUBLIC_API_URL = (paste your Railway URL from Step 3)
   ```
6. Click **Deploy** — Vercel builds and gives you a live URL!
   - It looks like: `https://fixit-buddy.vercel.app`

---

## STEP 5 — Test Your Live App

Open your Vercel URL and try this:

1. Type **"Fairphone"** in the search box and press Enter
2. Click **Fairphone 5** from the results
3. Switch to the **💬 AI Chat** tab
4. Ask: *"How do I replace the battery?"*
5. Upload a PDF repair manual (optional) for more accurate answers
6. Switch to **🔩 Parts** tab to see EU price compliance

---

## Running Locally (optional)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
uvicorn main:app --reload
# API is now at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# App is now at http://localhost:3000
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "CORS error" in browser | Add your Vercel URL to `allow_origins` in `backend/main.py` |
| "Gemini API error" | Check your `GEMINI_API_KEY` in Railway variables |
| Railway build fails | Make sure Root Directory is set to `backend` |
| Vercel build fails | Make sure Root Directory is set to `frontend` |
| Chat gives no answer | Backend might be sleeping — Railway free tier sleeps after inactivity, just wait 30s |

---

## Upgrading Later

- **Connect real EU DPP API**: replace mock data in `routers/score.py`
- **Add more devices**: add entries to the `DEVICES` dict in `routers/score.py`
- **Add user accounts**: add Auth.js to the frontend
- **Better vector storage**: swap FAISS for Pinecone (free tier available)
