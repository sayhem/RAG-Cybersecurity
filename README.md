# Cybersecurity RAG 

A local web application that answers cybersecurity questions or short incident descriptions using evidence from the **ChromaDB** database. It uses one sequential CrewAI crew containing exactly three agents and refuses unrelated requests before any document search or answer generation occurs.

## How it works

```text
One Crew -> Categorization Agent
                 |
                 +-> unrelated -> stop with scope message
                 |
                 +-> question/incident -> Retrieval Agent -> relevant document chunks
                                                       -> Response Agent -> cited answer
```


## The three agents

1. **Categorization Agent** routes input to `cybersecurity_question`, `incident_description`, or `unrelated`. It does not retrieve or answer.
2. **Retrieval Agent** has exactly one custom tool. That tool searches the appropriate Chroma collection and returns about five passages with citation metadata. It does not create the final answer.
3. **Response Agent** sees only the input, category, and retrieved evidence. It creates a sourced answer or incident analysis response using **ONLY** the retrieved document and not using its pretrained knowledge.

All three agents and all three tasks belong to the same `Crew` with
`Process.sequential`. The retrieval and response tasks are conditional: unrelated
input skips both tasks, while relevant input flows from Agent 1 to Agent 2 to Agent 3.

Two collections prevent reference material from being mixed indiscriminately with incident-response evidence:

- `cybersecurity_questions` contains material used for security questions.
- `incident_response` contains material used for possible incident descriptions.

PDF, Markdown, and Excel files can coexist in either collection. Collections are semantic, not file-type-specific.

## Project files

- `app.py` — Streamlit browser interface.
- `agents.py` — direct Python definitions for all three agents, their tasks, and branching logic.
- `retrieval_tool.py` — the retrieval agent's single custom Chroma search tool.
- `ingest.py` — document readers, chunking, metadata, embeddings, and Chroma upserts.
- `config.py` — `.env`, model, embedding, and path settings.
- `data/cybersecurity_questions/` — source documents for questions.
- `data/incident_response/` — source documents for incident analysis.
- `data/shared/` — common sources indexed into both collections without duplicate files.
- `requirements.txt` — Python dependencies.
- `Dockerfile` and `docker-compose.yml` — container build and local service configuration.

## How documents are processed

- **PDF:** PyMuPDF (`fitz`) reads each page. The page number is saved for citations.
- **Markdown:** UTF-8 text is grouped under heading paths such as `Broken Access Control > Prevention`. That path becomes section metadata.
- **Excel:** pandas and openpyxl turn each data row into a readable `Column: value` record.

Long records are chunked. Chunks are embedded and written in batches. Source hashes let unchanged files be skipped on later runs; changed files replace their old chunks.

## Option A: Run with Docker (recommended)

Install Docker Desktop first and make sure it is open and running, then run these commands from this project folder.

1. Create the environment file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and replace `your_google_api_key_here` with your Google API key.

3. Build the image:

   ```bash
   docker compose build
   ```

4. Ingest the documents. The embedding model is downloaded the first time:

   ```bash
   docker compose run --rm cybersecurity-rag uv run --no-sync python ingest.py
   ```

5. Launch the application:

   ```bash
   docker compose up
   ```

6. Open [http://localhost:8501](http://localhost:8501). Stop it with `Ctrl+C`.

The `data/` directory is mounted read-only and `chroma_db/` is mounted for persistence, so the database survives container recreation.

## Option A2: Develop in VS Code Dev Containers

This is the easiest workflow when you want VS Code itself to work inside Docker.

1. Install Docker Desktop, VS Code, and the VS Code extension **Dev Containers**
   (`ms-vscode-remote.remote-containers`).
2. Start Docker Desktop.
3. Open this project folder in VS Code.
4. Press `Command+Shift+P` and choose **Dev Containers: Reopen in Container**.
5. Wait for the first build to finish. The first build installs the dependencies
   with uv and can take several minutes. VS Code then reconnects inside `/workspace`.
6. Open `.env` and replace the placeholder Google API key. The container creates
   `.env` from `.env.example` automatically when it is missing.
7. Press `Command+Shift+P`, choose **Tasks: Run Task**, and run
   **RAG: Ingest documents** once.
8. Run **Tasks: Run Task** again and select **RAG: Start Streamlit**.
9. VS Code forwards port 8501 and opens the application. If it does not open,
   visit [http://localhost:8501](http://localhost:8501).

The integrated terminal is already inside the development container. You can also
run the two tasks manually:

```bash
uv run --no-sync python ingest.py
uv run --no-sync streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

After changing `pyproject.toml`, run **Dev Containers: Rebuild Container** so the
environment in `/opt/venv` is rebuilt. Source-code changes appear immediately and
do not require rebuilding the container.

## Option B: Run locally with uv

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required. The Docker workflow
already includes uv, so these commands are only for running without Docker.

```bash
uv sync
cp .env.example .env
```

Edit `.env` and add the API key, then run:

```bash
uv run python ingest.py
uv run streamlit run app.py
```

Streamlit prints the local browser URL, normally [http://localhost:8501](http://localhost:8501).


## Test cases

### Test 1: Security question

Input: `What is broken access control?`

Expected category: `cybersecurity_question`. The answer should use evidence from `cybersecurity_questions` and end with sources.

### Test 2: Incident description

Input: `Security monitoring detected a newly created scheduled task that launches an unfamiliar executable whenever a user logs in. What attacker behavior could this indicate?`

Expected category: `incident_description`. The response should provide an interpretation based on evidence retrieved from the `incident_response` collection.

### Test 3: Unrelated input

Input: `How do I cook pasta?`

Expected category: `unrelated`, followed by:

> This system only answers cybersecurity-related questions or analyzes short cybersecurity incident descriptions.

The retrieval and response agents do not run.



## Configuration

`.env.example` documents all settings:

- `GOOGLE_API_KEY` authenticates the default Gemini model.
- `MODEL_NAME` is a LiteLLM-style CrewAI model identifier. Change it without editing Python.
- `EMBEDDING_MODEL` must stay the same for ingestion and retrieval. If it changes, rebuild `chroma_db/`.
- `CHROMA_PATH` controls where the persistent index is stored. Docker overrides it to `/app/chroma_db`.


## Adding or rebuilding documents

Place `.pdf`, `.md`, or `.xlsx` files beneath the appropriate directory:

```text
data/
├── cybersecurity_questions/
├── incident_response/
└── shared/
```

Put a document in `data/shared/` when both retrieval collections should use it.

After adding or changing files, run `uv run python ingest.py` locally or the Docker ingestion command again. Existing stable chunk IDs are updated. To fully rebuild, stop the app, delete only the generated `chroma_db/` directory, and rerun ingestion:

```bash
rm -rf ./chroma_db
uv run python ingest.py
```

Run the command from this project's root and delete only `./chroma_db`.