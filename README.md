# MapleVitals

*A Canadian public-health intelligence platform, built one layer at a time.*

Ask MapleVitals a question about Canadian public-health data in plain English —
e.g. *"How has diabetes prevalence changed by province since 2015?"* — and it
figures out the analysis, runs it, and returns a chart with a short interpretation
grounded in the real source.

> **Status:** 🚧 Early development (Milestone 0). Right now it loads a StatCan
> health dataset and uses an LLM to describe it in plain English. Agentic
> analysis, RAG grounding, and a live UI are on the roadmap below.

## Roadmap
- [x] **M0** — Load a Canadian health CSV, get an LLM to describe it
- [ ] **M1** — Plain-English question → agent writes & runs pandas/matplotlib → chart + interpretation
- [ ] **M2** — RAG grounding with citations (ChromaDB)
- [ ] **M3** — Agent fetches its own data via the StatCan API (LangGraph)
- [ ] **M4** — Persistence + multi-turn memory (SQL)
- [ ] **M5** — Streamlit UI + evaluator agent
- [ ] **M6** — Deploy (FastAPI + Docker, live link)

## Setup
```bash
conda create -n maplevitals python=3.12 -y
conda activate maplevitals
pip install pandas anthropic python-dotenv
pip install matplotlib
```

Then create a `.env` file with your API key:
```
OPENAI_API_KEY=sk-your-key-here
```

## Data
Uses StatCan table **13-10-0096** — "Health characteristics, annual estimates."
Download the CSV from statcan.gc.ca and place it at `data/health.csv`.

## Tech
Python · pandas · OpenAI API
