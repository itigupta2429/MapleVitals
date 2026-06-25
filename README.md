<picture>
  <source media="(prefers-color-scheme: dark)" srcset="logo/maplevitals-lockup-dark.svg">
  <img src="logo/maplevitals-lockup-light.svg" alt="MapleVitals – Canadian public-health intelligence" width="380">
</picture>

Ask MapleVitals a question about Canadian public-health data in plain English —
e.g. *"How has diabetes prevalence changed by province since 2015?"* — and it
figures out the analysis, runs it, and returns a chart with a short interpretation
grounded in the real source.

> **Status:** ✅ Live Streamlit app with verified agent outputs, interactive charts, and a province-level choropleth map. Agentic live querying, RAG grounding, and multi-turn memory are on the roadmap below.

## Showcase

- Fair/poor mental health by age & gender in Alberta (2015–2024)
- Heavy drinking trends in Alberta among 18–34 year olds
- Smoking rates among young adults
- Self-reported obesity ranked by province (2024)
- Healthcare access vs. self-rated health in Alberta

## Roadmap

![M0](https://img.shields.io/badge/M0-complete-brightgreen) Load StatCan CSV, LLM describes it in plain English  
![M1](https://img.shields.io/badge/M1-complete-brightgreen) Question → agent analysis → chart + interpretation  
![M2](https://img.shields.io/badge/M2-complete-brightgreen) Streamlit UI, choropleth map, dark/light theme, data-quality flags  
![M3](https://img.shields.io/badge/M3-planned-lightgrey) RAG grounding with citations (ChromaDB)  
![M4](https://img.shields.io/badge/M4-planned-lightgrey) Agent fetches live StatCan API data (LangGraph)  
![M5](https://img.shields.io/badge/M5-planned-lightgrey) Multi-turn persistence and memory (SQL)  
![M6](https://img.shields.io/badge/M6-planned-lightgrey) FastAPI + Docker, public deployment

## Setup

```bash
conda create -n maplevitals python=3.12 -y
conda activate maplevitals
pip install streamlit plotly pandas
```

Then run:
```bash
streamlit run app.py
```

## Data

Uses StatCan table **13-10-0096** — "Health characteristics, annual estimates."
Download the CSV from statcan.gc.ca and place it at `data/health.csv`.

## Tech

Python · Pandas · Plotly · Streamlit
