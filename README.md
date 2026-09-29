# 🚗 Melbourne Dealership SQL-RAG Assistant

An internal, deterministic Text-to-SQL Retrieval-Augmented Generation (RAG) system built to query over **500,000+ indexed vehicle records** across three dealership branches in Melbourne, Victoria (Melbourne CBD, Doncaster, and Dandenong).

The system operates completely offline using local open-weight language models via **LM Studio**, orchestrated with **FastAPI**, tracked with an **Observability & Tracing layer**, evaluated via **Ragas**, and presented through an interactive **Streamlit Chat UI**.

---

## 🏛️ System Architecture

```text
[ Streamlit Chat UI ] (Port 8501)
            │
            ▼
[ FastAPI Backend ] (Port 8001)
            │
            ├── 1. Domain Intent Guardrail
            │
            ├── 2. Text-to-SQL Translation
            │        └──► [ LM Studio: Qwen 2.5 / Gemma 3n ] (Port 1234)
            │
            ├── 3. Read-Only Query Sanitizer
            │
            ├── 4. Relational Data Query
            │        └──► [ PostgreSQL 16 ] (500k records, GIN/B-Tree Indexes)
            │
            ├── 5. Response Synthesis
            │        └──► [ LM Studio: Qwen 2.5 / Gemma 3n ]
            │
            ├── 6. Audit & Observability
            │        └──► [ SQLite Traces Store ]
            │
            └── 7. Automated Benchmarking
                     └──► [ Ragas + HuggingFace Embeddings ]
```

---

## ✨ Features

* **High-Performance Dataset:** Scalable PostgreSQL schema populated with 500,000 realistic dummy records across 50+ real automotive brands.
* **Strict Guardrails:** Detects and politely rejects out-of-scope/unrelated questions such as general trivia, history, and non-dealership queries before running SQL queries.
* **Deterministic SQL Generation:** Uses prompt-guided PostgreSQL `SELECT` queries with case-insensitive `ILIKE` pattern matching.
* **Full Observability & Audit Trail:** Automatically logs every incoming question, generated SQL, execution latency, and context payloads into SQLite.
* **Automated Ragas QA:** Quantitative scoring for **Faithfulness** and **Answer Relevancy** using local LLM judges and `sentence-transformers` embeddings.
* **ChatGPT-Style Chat UI:** Pinned bottom input bar, upward-scrolling chat history, and tabbed inspection for system observability and evaluation.

---

## 📁 Project Structure

```text
dealership-sql-rag/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Environment and model configurations
│   │   ├── database.py         # SQLAlchemy engine & read-only execution
│   │   ├── evaluation.py       # Ragas evaluation using local LLM & embeddings
│   │   ├── observability.py    # SQLite audit logging and trace retriever
│   │   └── rag_engine.py       # Guardrails, Text-to-SQL, and synthesis
│   └── main.py                 # FastAPI endpoints
├── frontend/
│   └── app.py                  # Streamlit chat interface & dashboard
├── .env                        # Environment variables (excluded from git)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Prerequisites

1. **Python 3.10 - 3.12**
2. **PostgreSQL 14+** running locally on port `5432`
3. **LM Studio** installed and serving models locally:

   * `qwen2.5-3b-instruct` (recommended for fast SQL translation)
   * `google/gemma-3n-e4b` (or similar instruction-tuned models)

---

## 🚀 Quick Start Guide

### 1. Database Setup & Data Ingestion

Log in to your PostgreSQL instance using `psql` or pgAdmin, and run the SQL setup script:

```sql
-- Creates branches, cars tables, GIN/B-tree indexes,
-- and generates 500,000 records
\i path/to/seed_data.sql
```

> **Note:** Ensure the `pg_trgm` extension is enabled if using trigram indexes.

---

### 2. Environment Setup

Clone the repository and set up a virtual environment:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment on Windows
.\.venv\Scripts\Activate.ps1

# Linux/macOS
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Configure `.env`

Create a `.env` file in the root directory:

```env
# PostgreSQL Database Credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here

# LM Studio Server
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_API_KEY=lm-studio

# Model Identifiers
SQL_LLM_MODEL=qwen2.5-3b-instruct
SYNTHESIS_LLM_MODEL=google/gemma-3n-e4b
```

---

### 4. Start LM Studio Local Server

1. Open **LM Studio**.
2. Go to the **Developer / Local Server** tab.
3. Load your selected model, for example:

   * `qwen2.5-3b-instruct`
   * `google/gemma-3n-e4b`
4. Ensure the server port is set to `1234`.
5. Start the server and verify that its status shows **Running**.

---

### 5. Start the FastAPI Backend

From the project root:

```powershell
uvicorn main:app --app-dir backend --reload --port 8001
```

The FastAPI API documentation will be available at:

```text
http://localhost:8001/docs
```

---

### 6. Launch the Streamlit Frontend

Open a **separate PowerShell terminal**, activate the virtual environment, and run:

```powershell
.\.venv\Scripts\Activate.ps1

streamlit run frontend/app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## 📊 Application Navigation

The Streamlit UI provides three operational tabs.

### 1. 💬 Dealership Assistant

Interactive chat interface for dealership-related questions, including:

* Vehicle stock
* Vehicle pricing
* Vehicle brands
* Vehicle models
* Dealership branches
* Vehicle specifications

Off-topic questions are rejected by the domain guardrail before SQL execution.

### 2. 📊 Observability & Tracing

Provides a live audit view containing:

* Recent user queries
* Generated SQL
* Execution latency
* Hallucination flags
* Context snapshots
* Query execution information

### 3. 🧪 Ragas Evaluation Engine

Automated evaluation runner for production traces.

The evaluation focuses on:

* **Faithfulness**
* **Answer Relevancy**

The evaluation pipeline uses local LLMs and HuggingFace sentence-transformer embeddings.

---

## 🛡️ Security & Performance Guardrails

### Read-Only SQL Enforcement

The system blocks destructive SQL operations before execution, including:

```text
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
GRANT
REVOKE
```

Only read-oriented SQL queries are permitted.

### Domain Guardrails

Questions unrelated to dealership vehicles, vehicle specifications, inventory, pricing, or Melbourne branches trigger an early exit.

This prevents unnecessary SQL execution and reduces the possibility of irrelevant model-generated responses.

### Index Optimization

The PostgreSQL database uses appropriate indexing strategies for high-volume vehicle searches, including:

* B-tree indexes
* GIN indexes
* Trigram indexes
* Composite indexes

Indexes can be applied to frequently queried fields such as:

```text
make
model
price_aud
branch_id
```

These indexes are designed to improve query performance across the 500,000+ vehicle records.

---

## 🔍 Example Queries

The assistant can handle questions such as:

```text
Show me all Toyota vehicles available in Doncaster.
```

```text
What cars are available under $30,000?
```

```text
How many BMW vehicles are currently in stock?
```

```text
Show me SUVs available at the Melbourne CBD branch.
```

```text
What is the average price of Mercedes vehicles?
```

```text
Which vehicles are available in Dandenong?
```

---

## 🧠 RAG / Text-to-SQL Workflow

The system follows the following pipeline:

```text
User Question
      │
      ▼
Domain Intent Guardrail
      │
      ├── Out of Scope ──► Rejection Response
      │
      ▼
Text-to-SQL Generation
      │
      ▼
SQL Sanitization
      │
      ├── Unsafe SQL ──► Reject
      │
      ▼
PostgreSQL Query Execution
      │
      ▼
Retrieved Database Context
      │
      ▼
Response Synthesis
      │
      ▼
Final Answer
      │
      ├──► Observability / SQLite Trace
      │
      └──► Ragas Evaluation
```

---

## 📈 Performance Considerations

The system is designed around a large relational dataset containing **500,000+ vehicle records**.

Performance considerations include:

* Indexed PostgreSQL columns
* Read-only database execution
* Restricted result sets
* SQL query sanitization
* Local LLM inference
* Separation of SQL generation and response synthesis
* SQLite-based observability
* Asynchronous FastAPI request handling where applicable

---

## 🔐 Environment Variables

The following environment variables are required:

| Variable              | Description                     | Example                    |
| --------------------- | ------------------------------- | -------------------------- |
| `DB_HOST`             | PostgreSQL host                 | `localhost`                |
| `DB_PORT`             | PostgreSQL port                 | `5432`                     |
| `DB_NAME`             | PostgreSQL database name        | `postgres`                 |
| `DB_USER`             | PostgreSQL username             | `postgres`                 |
| `DB_PASSWORD`         | PostgreSQL password             | `your_password_here`       |
| `LM_STUDIO_BASE_URL`  | LM Studio OpenAI-compatible API | `http://127.0.0.1:1234/v1` |
| `LM_STUDIO_API_KEY`   | LM Studio API key               | `lm-studio`                |
| `SQL_LLM_MODEL`       | Model used for SQL generation   | `qwen2.5-3b-instruct`      |
| `SYNTHESIS_LLM_MODEL` | Model used for answer synthesis | `google/gemma-3n-e4b`      |

> **Security:** Never commit `.env` to source control. Add `.env` to `.gitignore`.

---

## 🧪 Testing the Backend

After starting the FastAPI server, open:

```text
http://localhost:8001/docs
```

The Swagger interface can be used to test the available API endpoints.

Example health check:

```text
GET /health
```

---

## 📝 Development Notes

The project is designed for local development and demonstration purposes.

The architecture separates the application into:

```text
Frontend
   ↓
FastAPI API
   ↓
RAG Engine
   ↓
Database Layer
   ↓
PostgreSQL
```

while the observability and evaluation components operate alongside the primary request pipeline.

---

## ⚠️ Important Notes

* PostgreSQL must be running before the backend starts processing database queries.
* LM Studio must have its local server running before SQL generation or response synthesis can occur.
* The database credentials in `.env` must match the local PostgreSQL configuration.
* The model identifiers must match models available in the local LM Studio installation.
* The application is designed to execute read-only SQL against the dealership database.
* Large result sets should be limited or paginated to avoid unnecessary memory consumption.

---

## 🏁 Running the Complete Application

Three components should be running:

### Terminal 1 — LM Studio

```text
LM Studio
└── Local Server
    └── Port 1234
```

### Terminal 2 — FastAPI

```powershell
.\.venv\Scripts\Activate.ps1

uvicorn main:app --app-dir backend --reload --port 8001
```

### Terminal 3 — Streamlit

```powershell
.\.venv\Scripts\Activate.ps1

streamlit run frontend/app.py
```

Then open:

```text
http://localhost:8501
```

The complete request flow is:

```text
Streamlit
    ↓
FastAPI
    ↓
Domain Guardrail
    ↓
LM Studio
    ↓
Generated PostgreSQL SELECT
    ↓
PostgreSQL
    ↓
Retrieved Vehicle Data
    ↓
LM Studio
    ↓
Final Response
    ↓
SQLite Observability
    ↓
Ragas Evaluation
```
