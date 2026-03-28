"""
rag_service.py — FixIt Buddy AI Core
Uses Gemini 1.5 Pro (long context) for RAG over repair manuals.

Two modes:
  1. PDF uploaded  → chunk with RecursiveCharacterTextSplitter
                     → embed with Gemini embedding-001
                     → store in FAISS
                     → retrieve top-k chunks → Gemini 1.5 Pro answers
  2. No PDF        → send question directly to Gemini 1.5 Pro (fallback)
"""

import os
import logging
from dotenv import load_dotenv

# Modern LangChain 0.2+ Imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA # This now works with the updated requirements
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set. "
        "Add it to your .env file or Railway environment variables."
    )

# ── Chunking settings ──────────────────────────────────────────────────────────
# chunk_size=600  keeps individual repair steps (screws, cables, torque) together
# chunk_overlap=80 ensures no instruction is cut off at a chunk boundary
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 80

# ── RAG prompt — plain-English repair instructions ────────────────────────────
RAG_SYSTEM_PROMPT = """You are FixIt Buddy, a warm, encouraging repair assistant.
Your job is to translate technical repair manuals into clear instructions that
anyone — a student, a parent, a first-time DIYer — can follow confidently.

Strict rules:
1. Replace ALL part codes with plain descriptions
   e.g. "Flex cable FPC-023" -> "the thin ribbon cable on the left side"
2. Replace ALL torque specs with everyday terms
   e.g. "0.6 N*m" -> "finger-tight, then a small quarter-turn"
3. Replace ALL tool model numbers with tool types
   e.g. "JIS #000 driver" -> "a very small Phillips screwdriver"
4. Add WARNING before every risky step (heat guns, adhesive, ESD, fragile cables)
5. End every step with a confidence check
   e.g. "Does it look like the photo? Perfect — you're doing great!"
6. If the manual doesn't cover something, say:
   "I'm not sure about that — the iFixit guide for this device has photos that help."
7. Never use words like torque, ESD, FPC, FPCB, SMD without explaining them first.
8. Keep your tone warm and friendly — repair anxiety is real and you defeat it!
"""

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=RAG_SYSTEM_PROMPT + """
--- Relevant section from the repair manual ---
{context}
-----------------------------------------------

User question: {question}

Your friendly, step-by-step answer (use numbered steps):""",
)

# ── Fallback prompt (no manual uploaded) ─────────────────────────────────────
FALLBACK_TEMPLATE = """{system}

The user is repairing a {device_name} and has asked:
"{question}"

Answer in numbered steps. Keep language simple and encouraging.
Add WARNING before any step that could damage the device or injure the user.
If you are unsure of a specific detail, say so and suggest iFixit as a reference."""


def _get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Return a Gemini 1.5 Pro LLM instance."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",           # Long-context model (1M token window)
        google_api_key=GEMINI_API_KEY,
        temperature=temperature,
        convert_system_message_to_human=True,  # Required for Gemini via LangChain
    )


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Return Gemini embedding model."""
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY,
    )


def ingest_pdf(pdf_path: str) -> FAISS:
    """
    Load a PDF repair manual, chunk it, embed it, return a FAISS vector store.

    Steps:
      1. PyPDFLoader reads every page
      2. RecursiveCharacterTextSplitter breaks text at natural boundaries
         (paragraphs -> sentences -> words) so screw sizes / cable names
         are never split across two chunks
      3. Gemini embedding-001 converts each chunk to a dense vector
      4. FAISS indexes all vectors for fast similarity search
    """
    logger.info(f"Ingesting PDF: {pdf_path}")

    # 1. Load
    loader = PyPDFLoader(pdf_path)
    pages  = loader.load()
    logger.info(f"  Loaded {len(pages)} pages")

    # 2. Split — order of separators matters:
    #    try to break at blank lines first, then single newlines,
    #    then sentences, then words — never mid-word
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    logger.info(f"  Split into {len(chunks)} chunks")

    # 3 + 4. Embed and index
    embeddings   = _get_embeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    logger.info("  FAISS index built successfully")

    return vector_store


def ask_rag(
    question:     str,
    device_name:  str,
    vector_store: FAISS | None = None,
) -> str:
    """
    Answer a repair question.

    If a vector_store is provided (PDF was uploaded):
      - Retrieve the 5 most relevant chunks from the manual
      - Feed them as context to Gemini 1.5 Pro with the RAG prompt
    Otherwise:
      - Ask Gemini 1.5 Pro directly using general repair knowledge
    """
    llm = _get_llm()

    if vector_store is not None:
        # RAG mode: manual is available
        logger.info(f"RAG mode — querying vector store for: {question[:60]}")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",           # stuff = inject all chunks into one prompt
            retriever=vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5},   # retrieve top-5 most relevant chunks
            ),
            chain_type_kwargs={"prompt": RAG_PROMPT},
            return_source_documents=False,
        )
        result = qa_chain.invoke({"query": question})
        return result["result"]

    else:
        # Fallback mode: no manual uploaded
        logger.info(f"Fallback mode — no manual for: {device_name}")
        prompt = FALLBACK_TEMPLATE.format(
            system=RAG_SYSTEM_PROMPT,
            device_name=device_name,
            question=question,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content


def summarise_manual(vector_store: FAISS, device_name: str) -> str:
    """
    Generate a short summary of what the uploaded manual covers.
    Called right after upload so the user knows what the AI can help with.
    """
    llm = _get_llm(temperature=0.1)

    # Grab a broad sample (top-10 chunks for "what does this manual cover")
    retriever  = vector_store.as_retriever(search_kwargs={"k": 10})
    sample_docs = retriever.invoke("what does this manual cover")
    sample_text = "\n\n".join(d.page_content for d in sample_docs)

    prompt = f"""You are FixIt Buddy. A user just uploaded a repair manual for their {device_name}.
Read this sample and write 2-3 friendly sentences summarising:
- What repairs / procedures this manual covers
- What tools it mentions
- Any important warnings to be aware of

Keep it simple and encouraging. Start with "Great news — your manual covers..."

Manual sample:
{sample_text[:3000]}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
