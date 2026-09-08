"""Shared settings for the application and ingestion pipeline."""

import os
from pathlib import Path

from crewai import LLM
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MODEL_NAME = os.getenv("MODEL_NAME", "gemini/gemini-3.5-flash-lite")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", str(BASE_DIR / "chroma_db"))).resolve()


# Make it easy to assign different models to individual agents later.
llm = LLM(model=MODEL_NAME, temperature=0.2)
categorization_llm = llm
retrieval_llm = llm
response_llm = llm

