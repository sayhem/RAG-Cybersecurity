"""Load PDF, Markdown, and Excel documents into persistent Chroma collections."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterator

import chromadb
import fitz
import pandas as pd
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from config import BASE_DIR, CHROMA_PATH, EMBEDDING_MODEL

DATA_DIR = BASE_DIR / "data"
SHARED_DATA_DIR = DATA_DIR / "shared"
COLLECTIONS = ("cybersecurity_questions", "incident_response")
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
BATCH_SIZE = 128


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    This function removes spaces and split text into smaller overlapping chunks.
    """
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Chunk size must be positive and overlap must be 0 <= overlap < size.")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Prefer a natural boundary without making a chunk dramatically short.
            boundary = max(text.rfind("\n", start + size // 2, end), text.rfind(". ", start + size // 2, end))
            if boundary > start:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks



# Document-reading functions for different datasets
def pdf_records(path: Path) -> Iterator[dict[str, Any]]:
    """This function reads text from each PDF page."""
    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                yield {"text": text, "page": page_number}


def markdown_records(path: Path) -> Iterator[dict[str, Any]]:
    """This functions reads Markdown text and keep its section heading."""
    headings: list[str] = []
    body: list[str] = []
    section = "Document introduction"

    def record() -> dict[str, Any] | None:
        text = "\n".join(body).strip()
        return {"text": text, "section": section} if text else None

    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            pending = record()
            if pending:
                yield pending
            body = []
            level = len(match.group(1))
            headings = headings[: level - 1]
            headings.append(match.group(2).strip())
            section = " > ".join(headings)
        else:
            body.append(line)
    pending = record()
    if pending:
        yield pending


def excel_records(path: Path) -> Iterator[dict[str, Any]]:
    """This function converts each Excel row into text."""
    workbook = pd.ExcelFile(path, engine="openpyxl")
    for sheet_name in workbook.sheet_names:
        frame = pd.read_excel(workbook, sheet_name=sheet_name, dtype=object)
        frame = frame.dropna(axis="columns", how="all")
        for zero_based_index, row in frame.iterrows():
            fields: list[str] = []
            for column, value in row.items():
                if pd.notna(value) and str(value).strip():
                    fields.append(f"{column}: {str(value).strip()}")
            if fields:
                # Header is Excel row 1, so the first data record is row 2.
                yield {"text": "\n".join(fields), "sheet": str(sheet_name), "row": int(zero_based_index) + 2}


def load_records(path: Path) -> Iterator[dict[str, Any]]:
    """Use the correct reader for the file type."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        yield from pdf_records(path)
    elif suffix == ".md":
        yield from markdown_records(path)
    elif suffix == ".xlsx":
        yield from excel_records(path)

#create a unique ID for each chunk.
def stable_id(category: str, relative_path: str, record_index: int, chunk_index: int) -> str:
    raw = f"{category}|{relative_path}|{record_index}|{chunk_index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    """Create a hash used to detect file changes."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_ingest_state(path: Path) -> dict[str, str]:
    """Load the hashes of previously processed files."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    valid_state = isinstance(value, dict) and all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    )
    return value if valid_state else {}


def save_ingest_state(path: Path, state: dict[str, str]) -> None:
    """Save the latest file hashes."""
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def batched(items: list[dict[str, Any]], size: int = BATCH_SIZE) -> Iterator[list[dict[str, Any]]]:
    """Divide items into smaller groups."""
    if size <= 0:
        raise ValueError("Batch size must be positive.")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def ingest_collection(
    client: chromadb.PersistentClient,
    category: str,
    embedding_function: SentenceTransformerEmbeddingFunction,
    state: dict[str, str],
    state_path: Path,
) -> tuple[int, int]:
    collection = client.get_or_create_collection(name=category, embedding_function=embedding_function)
    folder = DATA_DIR / category
    count = 0
    skipped_files = 0

    source_paths = sorted(
        path
        for source_folder in (folder, SHARED_DATA_DIR)
        for path in source_folder.rglob("*")
        if path.suffix.lower() in {".pdf", ".md", ".xlsx"}
    )
    for path in source_paths:
        if path.is_relative_to(SHARED_DATA_DIR):
            relative_path = f"shared/{path.relative_to(SHARED_DATA_DIR).as_posix()}"
        else:
            relative_path = path.relative_to(folder).as_posix()
        source_hash = file_sha256(path)
        state_key = f"{category}/{relative_path}"
        existing_ids: list[str] = []
        if state.get(state_key) == source_hash:
            existing = collection.get(
                where={"$and": [{"source": relative_path}, {"source_hash": source_hash}]},
                limit=1,
                include=["metadatas"],
            )
            existing_ids = existing["ids"]
        if existing_ids:
            skipped_files += 1
            print(f"  Unchanged, skipping {category}/{relative_path}")
            continue

        # Delete the old chunks before adding the updated document.
        print(f"  Processing {category}/{relative_path}")
        collection.delete(where={"source": relative_path})
        pending: list[dict[str, Any]] = []
        for record_index, record in enumerate(load_records(path)):
            for chunk_index, chunk in enumerate(chunk_text(record["text"])):
                # Store source details so they can be shown in citations.
                metadata: dict[str, str | int | float | bool] = {
                    "source": relative_path,
                    "source_hash": source_hash,
                }
                for key in ("page", "section", "sheet", "row"):
                    value = record.get(key)
                    if value not in (None, ""):
                        metadata[key] = value
                pending.append(
                    {
                        "id": stable_id(category, relative_path, record_index, chunk_index),
                        "document": chunk,
                        "metadata": metadata,
                    }
                )
                count += 1

        for batch in batched(pending):
            collection.upsert(
                ids=[item["id"] for item in batch],
                documents=[item["document"] for item in batch],
                metadatas=[item["metadata"] for item in batch],
            )
        state[state_key] = source_hash
        save_ingest_state(state_path, state)
        print(f"  Indexed {len(pending)} chunks from {relative_path}")
    return count, skipped_files


def main() -> None:
    # Store the database on disk so it can be reused later.
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    state_path = CHROMA_PATH / "ingest_state.json"
    state = load_ingest_state(state_path)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    #embedding is done by model of choice
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    SHARED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for category in COLLECTIONS:
        folder = DATA_DIR / category
        folder.mkdir(parents=True, exist_ok=True)
        count, skipped_files = ingest_collection(client, category, embedding_function, state, state_path)
        print(f"Upserted {count} chunks into {category}; skipped {skipped_files} unchanged files.")


if __name__ == "__main__":
    main()
