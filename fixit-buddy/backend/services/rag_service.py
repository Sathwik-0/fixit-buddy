import os
import logging
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHUNK_SIZE    = 600
CHUNK_OVERLAP = 80

RAG_SYSTEM_PROMPT = """You are FixIt Buddy, a warm, encouraging repair assistant.
Your job is to translate technical repair manuals into clear instructions that
anyone — a student, a parent, a first-time DIYer — can follow confidently.

Strict rules:
1. Replace ALL part codes with plain descriptions
2. Replace ALL torque specs with everyday terms e.g. finger-tight
3. Replace ALL tool model numbers with tool types
4. Add WARNING before every risky step
5. End every step with a confidence check e.g. "Does it look right? Great!"
6. Keep your tone warm and friendly!
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

FALLBACK_TEMPLATE = """{system}

The user is repairing a {device_name} and has asked:
"{question}"

Answer in numbered steps. Keep language simple and encouraging.
Add WARNING before any risky step.
If unsure, suggest iFixit as a reference."""


def _get_llm(temperature: float = 0.3) -> ChatGroq:
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=GROQ_API_KEY,
        temperature=temperature,
    )


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=OPENAI_API_KEY,
    )


def ingest_pdf(pdf_path: str) -> FAISS:
    logger.info(f"Ingesting PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    pages  = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    logger.info(f"  Split into {len(chunks)} chunks")

    embeddings   = _get_embeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    logger.info("  FAISS index built successfully")
    return vector_store


def ask_rag(
    question:     str,
    device_name:  str,
    vector_store: FAISS | None = None,
) -> str:
    llm = _get_llm()

    if vector_store is not None:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5},
            ),
            chain_type_kwargs={"prompt": RAG_PROMPT},
            return_source_documents=False,
        )
        result = qa_chain.invoke({"query": question})
        return result["result"]
    else:
        prompt = FALLBACK_TEMPLATE.format(
            system=RAG_SYSTEM_PROMPT,
            device_name=device_name,
            question=question,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content


def summarise_manual(vector_store: FAISS, device_name: str) -> str:
    llm = _get_llm(temperature=0.1)
    retriever   = vector_store.as_retriever(search_kwargs={"k": 10})
    sample_docs = retriever.invoke("what does this manual cover")
    sample_text = "\n\n".join(d.page_content for d in sample_docs)

    prompt = f"""You are FixIt Buddy. A user uploaded a repair manual for {device_name}.
Summarise in 2-3 friendly sentences what repairs it covers and what tools are needed.
Start with "Great news — your manual covers..."

Manual sample:
{sample_text[:3000]}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
