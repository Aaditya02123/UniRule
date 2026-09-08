# UniRule

An AI-powered question-answering system over a university rulebook corpus, designed to answer questions using grounded evidence while explicitly detecting contradictions and unsupported questions.

> **Core idea:** A university rulebook should not be treated as a single source of truth when different documents or sections can disagree with each other.

UniRule retrieves relevant passages, preserves their document and section context, and is designed to distinguish between:

- `ANSWERED` — the corpus contains sufficient evidence to answer the question.
- `CONFLICT` — relevant sources contain contradictory rules.
- `NOT_COVERED` — the corpus does not contain sufficient evidence to answer the question.

---

## Problem Statement

UniRule is a QA service over a university rulebook corpus.

The system is designed to:

1. Accept a natural-language question.
2. Retrieve relevant passages from the university rulebook.
3. Ground responses in retrieved evidence.
4. Provide source passages, section references, and similarity scores.
5. Detect contradictions between different parts of the rulebook.
6. Reject questions that are not covered by the corpus.

The project uses a synthetic university corpus representing **Medicaps University**.

---

## Current Project Status

### Completed

- [x] Phase 1 — Project scaffolding
- [x] Phase 2 — Synthetic university rulebook corpus
- [x] Phase 3 — Multi-format document ingestion
- [x] Phase 4 — Structure-aware chunking
- [x] Phase 5 — Embedding pipeline
- [x] Phase 5.5 — Local embedding provider
- [x] Phase 6 — Retrieval quality validation and tuning
- [x] Automated test suite — 35 tests passing

### Upcoming

- [ ] Evidence analysis and contradiction classification
- [ ] Grounded answer generation
- [ ] FastAPI `/ask` endpoint
- [ ] Frontend integration
- [ ] End-to-end evaluation
- [ ] Final documentation and demo preparation

---

# Architecture

```text
                    Medicaps University Corpus
                    ┌─────────┬─────────┬─────────┐
                    │   PDF   │   MD    │   CSV   │
                    └────┬────┴────┬────┴────┬────┘
                         │         │         │
                         └─────────┼─────────┘
                                   ↓
                         ┌──────────────────┐
                         │ Document         │
                         │ Ingestion        │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Structure-Aware  │
                         │ Chunking         │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Embedding        │
                         │ Provider         │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
          Local SentenceTransformer       OpenAI Optional
          (default / zero-cost)            (optional)
                    │
                    └─────────────┬─────────────┘
                                  ↓
                         ┌──────────────────┐
                         │ NumPy Vector     │
                         │ Index            │
                         └────────┬─────────┘
                                  ↑
                                  │
                           User Question
                                  │
                                  ↓
                         ┌──────────────────┐
                         │ Query Embedding  │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Top-K Retrieval  │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Evidence         │
                         │ Analysis         │
                         └────────┬─────────┘
                                  ↓
                  ┌───────────────┼───────────────┐
                  ↓               ↓               ↓
              ANSWERED        CONFLICT       NOT_COVERED
                  │               │               │
                  └───────────────┼───────────────┘
                                  ↓
                         Grounded Response
                                  ↓
                         FastAPI `/ask`
                                  ↓
                         Vanilla JS UI
```

---

# Project Structure

```text
UniRule/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── ingestion.py
│       ├── chunking.py
│       ├── embeddings.py
│       ├── index.py
│       ├── retrieval.py
│       ├── evidence_analyzer.py
│       └── answer_generator.py
│
├── data/
│   ├── academic_regulations.pdf
│   ├── examination_policy.md
│   ├── fee_schedule.csv
│   ├── hostel_handbook.pdf
│   ├── medical_exemptions.md
│   ├── scholarship_policy.md
│   ├── student_discipline.md
│   ├── contradictions.json
│   └── .keep
│
├── storage/
│   ├── embeddings.npy
│   └── metadata.json
│
├── scripts/
│   ├── generate_corpus.py
│   ├── ingest.py
│   └── validate_retrieval_quality.py
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_chunking.py
│   ├── test_embeddings.py
│   ├── test_retrieval.py
│   └── evaluation/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

---

# Corpus

The current synthetic corpus contains **7,500+ words** across multiple document formats.

The corpus deliberately contains realistic university policies as well as three planted contradictions.

### Corpus Documents

| Document | Format | Approx. Words |
|---|---|---:|
| Academic Regulations | PDF | 2,452 |
| Examination Policy | Markdown | 676 |
| Fee Schedule | CSV | 801 |
| Hostel Handbook | PDF | 1,008 |
| Medical Exemptions | Markdown | 1,180 |
| Scholarship Policy | Markdown | 560 |
| Student Discipline | Markdown | 832 |
| **Total** | | **7,500+** |

---

# Planted Contradictions

Three real contradictions have been deliberately planted in the corpus.

## 1. Attendance Requirement

### Academic Regulations

The academic regulations state a hard minimum attendance requirement of **75%**, with no general exception for medical circumstances.

### Medical Exemptions

The medical exemptions policy states that students with an approved Type A medical certificate may be considered with attendance as low as **60%**.

```text
75% minimum attendance
        VS
60% possible attendance with approved medical documentation
```

---

## 2. Fee Payment Deadline

### Academic Regulations

The academic regulations specify **July 15** as the fee payment deadline.

### Fee Schedule

The fee schedule CSV specifies **July 31** as the applicable deadline.

```text
July 15
   VS
July 31
```

---

## 3. Hostel Curfew

### Hostel Handbook

The hostel handbook requires undergraduate hostel residents to return by **10:00 PM**.

### Student Discipline Policy

The student discipline policy states that students may remain outside until **11:00 PM** on ordinary days.

```text
10:00 PM
   VS
11:00 PM
```

### Important Design Principle

UniRule does **not** automatically assume that one conflicting rule overrides the other.

When conflicting evidence is retrieved, the system should surface the disagreement rather than inventing a priority that is not explicitly established by the corpus.

---

# Document Ingestion

UniRule supports ingestion from:

- PDF
- Markdown
- CSV

The ingestion layer converts these different formats into a common structured representation.

Each document record preserves metadata such as:

- Document name
- Source path
- File type
- Section
- Page where applicable
- Content
- Structural context

### PDF

PDF documents are processed page-by-page using PyMuPDF.

### Markdown

Markdown headings are used to preserve section structure.

### CSV

CSV rows are converted into sentence-like records while retaining relevant row information.

The ingestion pipeline is deterministic and processes the corpus in a stable order.

---

# Structure-Aware Chunking

The ingestion records are converted into retrieval-ready chunks.

The chunking strategy attempts to preserve:

- Document boundaries
- Section boundaries
- Page boundaries
- Logical context

Chunks are split when necessary to avoid excessively large retrieval units.

Current corpus transformation:

```text
330 initial ingestion records
        ↓
Structure-aware chunking
        ↓
270 final chunks
```

All final chunks are below the configured maximum chunk size.

Chunk IDs are generated deterministically using SHA-256-based identifiers.

This ensures that repeated ingestion produces stable chunk identifiers.

---

# Embeddings

UniRule uses an embedding-provider abstraction so that the retrieval system is not tightly coupled to one embedding service.

Currently supported providers:

## Local — Default

```text
sentence-transformers/all-MiniLM-L6-v2
```

The local provider produces:

```text
270 chunks × 384 dimensions
```

The local provider is the default because it allows the project to run without API credits.

## OpenAI — Optional

An OpenAI embedding provider is also implemented as an optional provider.

Example configuration:

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

The same configured embedding provider is used for both:

1. Corpus embeddings
2. Query embeddings

This ensures that query and document vectors exist in the same embedding space.

---

# Vector Storage

UniRule intentionally avoids an external vector database.

Embeddings are stored using NumPy:

```text
storage/
├── embeddings.npy
└── metadata.json
```

The vector index uses cosine similarity for retrieval.

This keeps the project lightweight and easy to run locally.

External vector databases such as Pinecone, Chroma, or FAISS are not required.

---

# Retrieval

The retrieval pipeline:

1. Embeds the user question.
2. Compares the query embedding against stored document embeddings.
3. Calculates cosine similarity.
4. Retrieves the highest-scoring chunks.
5. Passes retrieved evidence to the later evidence-analysis stage.

Current retrieval configuration:

```env
RETRIEVAL_TOP_K=30
RETRIEVAL_MIN_SCORE=0.55
```

The relatively broad retrieval window is intentional.

The system needs to retrieve enough evidence to discover disagreements between documents.

For example:

```text
Document A → rank 1
Document B → rank 25
```

Retrieving only the top few passages could miss the second side of a contradiction.

The architecture therefore follows:

> **Retrieve broadly enough to discover disagreement, then reason narrowly over the retrieved evidence.**

---

# Retrieval Quality Validation

A dedicated validation script is included:

```text
scripts/validate_retrieval_quality.py
```

The validation covers:

### Attendance contradiction

Checks whether both:

- 75% requirement
- 60% medical exception

can be retrieved.

### Hostel contradiction

Checks whether both:

- 10 PM curfew
- 11 PM ordinary-day rule

can be retrieved.

### Fee contradiction

Tests retrieval of:

- July 15 deadline
- July 31 deadline

The fee case is particularly important because the CSV contains many similar rows that can crowd the retrieval results.

### Unanswerable question

A question about an unsupported topic, such as laptop policy, is used to verify that irrelevant corpus content is not incorrectly treated as evidence.

---

# Retrieval Tuning Results

The initial retrieval configuration was:

```env
RETRIEVAL_TOP_K=8
RETRIEVAL_MIN_SCORE=0.60
```

Testing showed:

- Attendance contradiction: retrieved successfully.
- Hostel contradiction: retrieved successfully.
- Fee contradiction: the second deadline could fall below the relevance threshold.
- Unsupported laptop question: correctly produced no sufficiently relevant evidence.

The configuration was therefore adjusted to:

```env
RETRIEVAL_TOP_K=30
RETRIEVAL_MIN_SCORE=0.55
```

This improved contradiction discovery, particularly for the fee schedule, while the unsupported laptop question remained below the relevance threshold.

Detailed findings are recorded in:

```text
validation_report.md
```

---

# Unanswerable Questions

The corpus also contains an evaluation set of **25 plausible questions that are intentionally not covered by the rulebook**.

These questions test whether the system can distinguish between:

```text
"I found something vaguely related"
```

and:

```text
"The corpus actually contains enough evidence to answer this."
```

The intended classification for these questions is:

```text
NOT_COVERED
```

This helps prevent hallucinated answers when the rulebook contains no relevant policy.

---

# Classification Model

The target QA pipeline uses three response classifications.

## ANSWERED

The retrieved evidence provides sufficient and non-conflicting information.

Example:

```text
Question:
"What is the minimum attendance requirement?"

Classification:
ANSWERED
```

---

## CONFLICT

The corpus contains materially contradictory evidence relevant to the question.

Example:

```text
Question:
"How much attendance is required when a student has a
Type A medical certificate?"

Retrieved evidence:
- Academic Regulations → 75%
- Medical Exemptions → 60%

Classification:
CONFLICT
```

The response should present both pieces of evidence rather than silently selecting one.

---

## NOT_COVERED

The corpus does not contain sufficient evidence.

Example:

```text
Question:
"What laptop specifications are required for first-year students?"

Classification:
NOT_COVERED
```

The system should avoid inventing a university policy in this situation.

---

# Planned Answer Contract

Each `/ask` response will ultimately provide:

```text
classification
answer
source passages
section references
similarity scores
```

Example:

```json
{
  "classification": "CONFLICT",
  "answer": "...",
  "sources": [
    {
      "document": "Academic Regulations",
      "section": "Attendance Requirements",
      "passage": "...",
      "similarity": 0.72
    },
    {
      "document": "Medical Exemptions",
      "section": "Medical Attendance Exceptions",
      "passage": "...",
      "similarity": 0.68
    }
  ]
}
```

The exact API schema will be finalized during the FastAPI implementation phase.

---

# Technology Stack

## Backend

- Python 3.12
- FastAPI
- Pydantic v2
- Uvicorn

## Document Processing

- PyMuPDF
- Python standard-library CSV processing

## Embeddings

- Sentence Transformers
- `sentence-transformers/all-MiniLM-L6-v2`
- Optional OpenAI embeddings

## Vector Processing

- NumPy
- Cosine similarity

## Frontend

- HTML
- CSS
- Vanilla JavaScript

## Testing

- pytest

## Configuration

- python-dotenv
- `.env` configuration

---

# Running the Project

## 1. Create the virtual environment

```powershell
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 2. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## 3. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

The default configuration uses local embeddings and does not require an OpenAI API key.

Example:

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
RETRIEVAL_TOP_K=30
RETRIEVAL_MIN_SCORE=0.55
DEBUG=true
```

---

## 4. Generate the corpus

```powershell
python scripts/generate_corpus.py
```

---

## 5. Run ingestion

```powershell
python scripts/ingest.py
```

---

## 6. Validate retrieval

```powershell
python scripts/validate_retrieval_quality.py
```

The validation results are documented in:

```text
validation_report.md
```

---

## 7. Run tests

Use:

```powershell
python -m pytest -q
```

Current status:

```text
35 passed
```

There is currently one harmless third-party deprecation warning from ReportLab.

Using:

```powershell
python -m pytest
```

is preferred over invoking `pytest` directly because it ensures the active Python environment is used correctly.

---

# Development Principles

### 1. Grounded over guessed

The system should only answer from evidence contained in the corpus.

### 2. Contradictions are first-class results

Conflicting rules should be surfaced instead of hidden.

### 3. No invented priority

If two policies conflict, the system should not claim that one overrides the other unless the corpus explicitly establishes that relationship.

### 4. Broad retrieval, narrow reasoning

Retrieval should be broad enough to discover competing evidence, while later reasoning should focus only on relevant passages.

### 5. Deterministic processing

Corpus ingestion, chunking, and chunk IDs should produce repeatable results.

### 6. Lightweight architecture

The project intentionally avoids unnecessary infrastructure such as:

- External vector databases
- Heavy orchestration frameworks
- React
- PostgreSQL
- Docker

The goal is to keep the system understandable, reproducible, and easy to demonstrate.

---

# Testing

The current automated test suite contains:

```text
35 tests
35 passed
0 failed
```

Tests currently cover areas including:

- Document ingestion
- PDF processing
- Markdown processing
- CSV processing
- Chunk creation
- Chunk ID determinism
- Embedding provider behavior
- Local embedding configuration
- Retrieval behavior
- Similarity calculations

Additional end-to-end tests will be added as the API and evidence-analysis layers are implemented.

---

# Roadmap

## Phase 7 — Evidence Analysis

Implement evidence-level reasoning to determine whether retrieved passages:

- Support the same answer
- Contain a contradiction
- Are insufficient

Output:

```text
ANSWERED
CONFLICT
NOT_COVERED
```

---

## Phase 8 — Grounded Answer Generation

Generate concise answers based only on the selected evidence.

For conflicts, present the competing rules clearly.

For unsupported questions, explicitly state that the corpus does not cover the requested information.

---

## Phase 9 — FastAPI API

Implement:

```http
POST /ask
```

The endpoint will accept a natural-language question and return the structured QA response.

---

## Phase 10 — Frontend

Build a simple Vanilla JS interface showing:

- Question input
- Answer
- Classification
- Source passages
- Sections
- Similarity scores
- Conflict warnings

---

## Phase 11 — End-to-End Evaluation

Evaluate the complete system against:

- Answerable questions
- Contradiction questions
- Unanswerable questions

---

## Phase 12 — Demo & Documentation

Prepare:

- Final README
- Architecture diagrams
- Evaluation results
- GitHub repository
- Working demonstration video

