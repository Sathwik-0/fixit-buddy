import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

RAG_SYSTEM_PROMPT = """You are FixIt Buddy, a warm, encouraging repair assistant.
Translate technical repair info into clear instructions for everyday people.

Rules:
1. Replace ALL part codes with plain descriptions
2. Replace ALL torque specs with everyday terms e.g. finger-tight
3. Add WARNING before every risky step
4. End every step with an encouraging check
5. Keep your tone warm and friendly!
"""

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


def ingest_pdf(pdf_path: str):
    logger.info(f"PDF received: {pdf_path}")
    return None


def ask_rag(question: str, device_name: str, vector_store=None) -> str:
    llm = _get_llm()
    prompt = FALLBACK_TEMPLATE.format(
        system=RAG_SYSTEM_PROMPT,
        device_name=device_name,
        question=question,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def summarise_manual(vector_store, device_name: str) -> str:
    llm = _get_llm(temperature=0.1)
    prompt = f"You are FixIt Buddy. Write 2 friendly sentences about helping repair {device_name}. Start with 'Great news!'"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
