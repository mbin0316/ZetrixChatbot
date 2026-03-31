# DOSM Household Income RAG Chatbot

A fully local RAG chatbot by Akmal over Malaysian Household Income statistics from [open.dosm.gov.my](https://open.dosm.gov.my), built with n8n, Qdrant, and Ollama. Answers questions with citation, handles off topic queries, and support CSV export.

---
## Demo Video

Watch the chatbot video git demonstration:

https://www.youtube.com/watch?v=a-zCZwmRfR8

## Quickstart (≤10 min)

**Prerequisites:** Python 3.x, Node.js, Docker, [Ollama](https://ollama.com), [n8n](https://n8n.io)


### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/dosm-chatbot.git
cd dosm-chatbot
```

### 2. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Pull Ollama models

```bash
ollama pull nomic-embed-text
ollama pull llama3.2
```

### 4. Ingest data

```bash
cd ingestion
pip install -r requirements.txt
python ingest.py
```

### 5. Start n8n and import workflow

```bash
n8n start
# Open http://localhost:5678
# Import workflow/dosm_chatbot.json
# Activate the workflow (toggle top-right)
```

### 6. Chat

```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{"chatInput": "What was Malaysia median income in 2022?"}'
```

Expected: `The median household income in Malaysia for 2022 was RM6,338. Data source: DOSM | open.dosm.gov.my | CC BY 4.0`

---

## Tool Choice & Model Provider

| Component        | Tool                          | Reason                                                    |
|------------------|-------------------------------|---------------------------------------------              |
| Workflow         | n8n (self-hosted)             | Chatbot layer,Visual flow builder, webhook support        |
| Vector Store     | Qdrant (local Docker)         | Fast metadata filtering, free, open-source                |
| Embeddings       | Ollama nomic-embed-text       | Local, no API key, 768-dim, strong semantic               |
| LLM              | Ollama llama3.2 / Groq API    | Local-first; Groq as fallback for tool use                |
| Ingestion        | Python + LangChain            | Flexible chunking and metadata control                    |
| Logging          | Google Sheets (n8n node)      | Zero-setup, easy to inspect                               |

> API keys: All models run locally via Ollama. Groq API key stored in `.env` (redacted in repo).

---

## Data Card

| Field            | Details                                                                 |
|------------------|-------------------------------------------------------------------------|
| Source           | [open.dosm.gov.my](https://open.dosm.gov.my) — Department of Statistics Malaysia |
| Dataset          | Household Income & Expenditure Survey                                   |
| License          | Creative Commons Attribution 4.0 (CC BY 4.0)                           |
| Last Updated     | 2024 (parlimen/DUN), 2022 (state/district/national)                     |
| Refresh Cadence  | Every 2 years (survey-based)                                            |
| Files Ingested   | 5 CSVs — national, state, district, parlimen, DUN                       |
| Total Rows       | 3,108                                                                   |
| Coverage         | 1970–2024 (national), 2019–2024 (sub-national)                         |
| Fields           | `date`, `income_mean`, `income_median`, geographic identifiers          |

---

## RAG Design

### Chunking Strategy

Each CSV rows is converted into a natural language sentence before chunking:

```
"In 2022, Selangor's mean household income was RM12,233 and median was RM9,983.
Source: hh_income_state.csv (DOSM)."
```

- **Chunk size:** 800 tokens
- **Chunk overlap:** 200 tokens
- **Splitter:** LangChain `RecursiveCharacterTextSplitter`
- **Rationale:** Row-level sentences keep facts atomic — one row = one fact = one chunk. Overlap ensures boundary chunks are not lost.

### Embeddings

- **Model:** `nomic-embed-text` via Ollama
- **Dimensions:** 768
- **Similarity:** Cosine distance

### Retrieval

- **k (top-k):** 8 chunks per query
- **Metadata filtering:** Qdrant payload indexes on `state`, `year`, `level` — enables precise filtering when state/year is mentioned in query
- **Fallback:** Pure vector search when no state/year detected in query

### Flow

```
User Query
    → Intent Check (topic guard)
    → RAG Search (embed query → Qdrant filter search)
    → LLM Generation (llama3.2 with context)
    → Confidence Check (low-confidence fallback)
    → Citation Formatter
    → Query Logger (Google Sheets)
    → Response
```

---

## Evaluation & Results

## Evaluation Scripts
 
| Script | Purpose | Usage |
|---|---|---|
| `eval/run_eval.py` | Sends all 15 queries to the webhook and records actual responses and latency | `python run_eval.py` |
| `eval/scoring.py` | Auto-scores each result by comparing expected RM figures against actual response | `python scoring.py` |
| `eval/calc_metrics.py` | Calculates hit rate, hallucination rate, correct rate, p50/p95 latency from scored results | `python calc_metrics.py` |
 
### How Scoring Works (`scoring.py`)
 
| Field | Logic |
|---|---|
| `hit` | `1` if `actual` is non-empty; `0` if empty or wrong refusal |
| `hallucinated` | `1` if `hit=1` and `correct=0` (answered but wrong) |
| `correct` | `1` if ≥ 50% of expected RM figures appear verbatim in the actual response; for responsible_ai queries, checks for refusal keywords |

### Results
These results now reflect real-world performance, with scoring and the scoring.py component providing the justification logic for retrieval hit rate, hallucination rate, and correctness. Previously, this logic was encapsulated within the n8n node workflow. The chatbot outputs were compared against the expected data(which is confirmed data beforehand) to assess accuracy and alignment of the chatbot.
 
| Metric | Score | Target | Status |
|---|---|---|---|
| Retrieval Hit Rate | 12 / 15 = **80.0%** | > 80% | ✅ Pass |
| Hallucination Rate | 1 / 15 = **6.7%** | < 10% | ✅ Pass |
| Correct Rate | 11 / 15 = **73.3%** | — | — |
| p50 Latency | **973ms** | < 2000ms | ✅ Pass |
| p95 Latency | **1239ms** | < 4000ms | ✅ Pass |
 
---

See `eval/queries.jsonl` for all 15 queries with expected answers and `eval/results.jsonl` for full results.

---

## Responsible AI

| Scenario                  | Handling                                                          |
|---------------------------|-------------------------------------------------------------------|
| Off topic query           | Topic guard blocks at Intent Check node, returns polite refusal  |
| Future date (e.g. 2030)   | LLM instructed to refuse projection not in dataset              |
| Low-confidence answer     | Confidence Check node detects uncertainty, asks for clarification |
| Missing data              | Returns "I cannot find that information" with DOSM source link   |
| Data disclaimer           | Every answer appended withh `Data source: DOSM | open.dosm.gov.my | CC BY 4.0` |

---

## Limitations & Future Work

**Current Limitations**

- Queries without a state name rely on pure vector search, which can return loosely related results
- llama3.2 struggles with multi-state comparison queries (sometimes only returns one state)
- Export feature is basic — returns a clarification prompt rather than a direct CSV download
- Latency is ~1.5–3s fully local; production deployment would benefit from a GPU

**Future Work**

- Add LangGraph for agentic retries and structured state handling
- Add MCP tool integration for export_csv and trend_summary actions
- Expand dataset to include expenditure and poverty data from DOSM
- Fine-tune embedding model on Malaysian economy terminology
- Add a chart/visualization node to return income trend graphs

---

## Project Structure

```
dosm-chatbot/
├── README.md
├── data_card.md
├── HOW_TO_RUN.txt
├── .env.example
├── datasets/
│   ├── hh_income.csv
│   ├── hh_income_state.csv
│   ├── hh_income_district.csv
│   ├── hh_income_parlimen.csv
│   └── hh_income_dun.csv
├── ingestion/
│   ├── ingest.py
│   ├── converters.py
│   ├── config.py
│   └── requirements.txt
├── workflow/
│   └── dosm_chatbot.json
└── eval/
    ├── queries.jsonl
    ├── results.jsonl
    ├── run_eval.py
    └── calc_metrics.py
```

---

## License

Data: CC BY 4.0 — Department of Statistics Malaysia  
Code: MIT
