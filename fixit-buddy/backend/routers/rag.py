"""
routers/rag.py — RAG endpoints for FixIt Buddy

POST /api/rag/upload/{session_id}  — upload a PDF repair manual
POST /api/rag/chat                 — ask a repair question (with or without manual)
GET  /api/rag/session/{session_id} — check if a session has a manual loaded
"""

import os
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.rag_service import ingest_pdf, ask_rag, summarise_manual

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory vector store cache keyed by session_id
# Production note: swap this for Redis + FAISS serialisation for multi-instance deploys
vector_stores: dict = {}


class ChatRequest(BaseModel):
    session_id: str
    question: str
    device_name: str = "your device"


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    used_manual: bool   # lets the frontend show "answered from your manual" badge


# ── Upload endpoint ────────────────────────────────────────────────────────────

@router.post("/upload/{session_id}")
async def upload_manual(session_id: str, file: UploadFile = File(...)):
    """
    Accept a PDF repair manual, run it through the RAG ingest pipeline,
    and store the FAISS vector store in memory for this session.

    Returns a friendly summary of what the manual covers so the user
    knows exactly what questions the AI can answer.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Try downloading a manual from iFixit.com."
        )

    # Validate file size (max 20 MB — Gemini can handle large manuals easily)
    MAX_BYTES = 20 * 1024 * 1024
    contents  = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is too large (max 20 MB). Try a smaller section of the manual."
        )

    # Save to /tmp for PyPDFLoader to read
    tmp_path = f"/tmp/fixit_{session_id}_{file.filename}"
    try:
        with open(tmp_path, "wb") as f:
            f.write(contents)

        # Run RAG ingest pipeline (chunk → embed → FAISS)
        logger.info(f"Ingesting manual for session {session_id}: {file.filename}")
        vector_store = ingest_pdf(tmp_path)
        vector_stores[session_id] = vector_store

        # Generate a friendly summary of what the manual covers
        # Uses Gemini 1.5 Pro to read a sample of the chunks
        from fastapi.concurrency import run_in_threadpool
        device_hint = "your device"   # frontend can pass this in future
        summary = await run_in_threadpool(
            summarise_manual, vector_store, device_hint
        )

        return {
            "status":     "ok",
            "session_id": session_id,
            "filename":   file.filename,
            "summary":    summary,
            "message":    "Manual uploaded and ready! Ask me anything about your repair.",
        }

    except Exception as e:
        logger.error(f"Ingest failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not read the PDF: {str(e)}. Make sure it's a text-based PDF (not a scan)."
        )
    finally:
        # Always clean up the temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Chat endpoint ──────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Answer a repair question using Gemini 1.5 Pro.

    If the session has an uploaded manual, the answer is grounded in
    those specific instructions (RAG mode).
    Otherwise, Gemini answers from general repair knowledge (fallback mode).
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    vector_store = vector_stores.get(req.session_id)   # None if no manual uploaded
    used_manual  = vector_store is not None

    try:
        from fastapi.concurrency import run_in_threadpool
        answer = await run_in_threadpool(
            ask_rag,
            req.question,
            req.device_name,
            vector_store,
        )
    except Exception as e:
        logger.error(f"RAG chat error for session {req.session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="The AI had trouble answering. Please try again."
        )

    return ChatResponse(
        answer=answer,
        session_id=req.session_id,
        used_manual=used_manual,
    )


# ── Session status endpoint ────────────────────────────────────────────────────

@router.get("/session/{session_id}")
def get_session_status(session_id: str):
    """Check whether a session has a manual loaded."""
    has_manual = session_id in vector_stores
    return {
        "session_id": session_id,
        "has_manual": has_manual,
        "message": "Manual is loaded and ready." if has_manual else "No manual uploaded yet.",
    }
