"""This tool is used to search the cybersecurity database and open the correct collection based on the category."""

from __future__ import annotations

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config import CHROMA_PATH, EMBEDDING_MODEL


class RetrievalInput(BaseModel):
    query: str = Field(..., description="The user's original text.")
    category: str = Field(..., description="cybersecurity_question or incident_description.")


class CybersecurityRetrievalTool(BaseTool):
    name: str = "search_authoritative_cybersecurity_documents"
    description: str = "Search the correct cybersecurity evidence collection using the query and category."
    args_schema: type[BaseModel] = RetrievalInput
    # returns this tool's exact document evidence as the retrieval task
    # result. This prevents the retrieval agent from replacing it with a category
    # label or an unsupported summary before the response agent receives it.
    result_as_answer: bool = True

    def _run(self, query: str, category: str) -> str:
        collection_name = {
            "cybersecurity_question": "cybersecurity_questions",
            "incident_description": "incident_response",
        }.get(category)
        if not collection_name:
            return "INVALID CATEGORY: retrieval is only permitted for cybersecurity inputs."
        if not CHROMA_PATH.exists():
            return "NO EVIDENCE DATABASE: run `python ingest.py` first."

        # Use the same embedding model that was used during ingestion.
        embedding_function = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        try:
            collection = client.get_collection(collection_name, embedding_function=embedding_function)
        except Exception:
            return f"NO EVIDENCE COLLECTION: {collection_name}. Run ingestion first."

        available = collection.count()
        if available == 0:
            return f"NO EVIDENCE FOUND in {collection_name}."
        results = collection.query(query_texts=[query], n_results=min(5, available))
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]

        formatted: list[str] = []
        for index, (document, metadata) in enumerate(zip(documents, metadatas), start=1):
            lines = [f"RESULT {index}", f"SOURCE: {metadata.get('source', 'Unknown')}"]
            for key in ("page", "section", "sheet", "row"):
                if key in metadata and metadata[key] not in (None, ""):
                    lines.append(f"{key.upper()}: {metadata[key]}")
            lines.extend(["CONTENT:", document])
            formatted.append("\n".join(lines))
        return "\n\n".join(formatted) if formatted else "NO EVIDENCE FOUND."
