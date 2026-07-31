# MapleVitals — Guiding Map

*A Canadian public-health agent platform, built one feature at a time.*

**For:** Iti · **Pace:** ~8–10 hrs/week · **Approach:** ship small and public, learn on the go.

> This is the living roadmap for all of MapleVitals — not tied to any one milestone. Update the **Status** line and the roadmap markers as you ship; the rest stays put unless the direction itself changes.

---

## Status (update as you go)

- ✅ M0 — data → LLM description
- ✅ M1 (v0.1) — question → chart + interpretation, **deployed** (Streamlit). LinkedIn post #1 live.
- ✅ MOAT validation layer active (`statcan_contract.yaml`).
- 🔨 **Currently on:** M2a — RAG grounding + citations (local).

---

## The 3 rules

1. **Build, don't binge.** Cap learning at ~3 hrs/week; spend the rest hands-on-keyboard. (Especially for cloud — learn the handful of services a feature needs, skip the rest.)
2. **One product, one repo, forever.** Every new skill is a *feature added*, not a new project. RAG, cloud, and any model you train all land inside MapleVitals.
3. **When lost, open the repo** — not another tutorial. Make the current "Done when" true.

---

## The product

Ask a Canadian health question in plain English → MapleVitals writes the analysis, runs it, returns a chart + a short interpretation grounded in — and cited to — the real source.

**Your edge:** your epidemiology background lets you judge when the output is *wrong*. Most builders can't. That's the story, and it has guardrails to point at.

---

## The guardrail trilogy (the moat)

Three different failures, three different guards:

1. **Quality** — *is the number reliable?* (`statcan_contract.yaml`: E-flags, suppression, comparability breaks.)
2. **Correctness** — *did we state the number we actually computed?* (print-before-report.)
3. **Definitional grounding** — *does the explanation match the documented source?* (RAG + citations.)

Quality ≠ correctness ≠ grounding. Keep them distinct.

---

## How you'll work

**Deploy first, then stack features.** Each feature = a version bump = one **build-log** LinkedIn post. Posting isn't gated on shipping, though — build-log is one of four pillars (build log · health insight · AI concept · opinion); the other three fill the weeks between releases. **The tracker is the source of truth for what to post next;** this doc sets build direction.

For **each piece**, be able to explain three things: **what** it does, **how** roughly (the flow), **where** it breaks and what guardrail you added. Go deep on the **agent loop + guardrails**; skip the boilerplate. Claude writes the code; you own the design, the guardrails, and the health-data judgment.

---

## The roadmap

Each row is one feature, one version, one post. Order can flex.

| Version | Feature | The new skill |
|---|---|---|
| ✅ — | M0: data → LLM description | LLM API calls |
| ✅ v0.1 | M1: question → chart + interpretation | agent loop, tool calling |
| ✅ v0.1‑live | Deploy M1 (Streamlit) | deployment, secrets, cost guardrails |
| 🔨 v0.2a | M2a: RAG grounding + citations (local) | embeddings, vector DB, RAG |
| ⏭ v0.2b | M2b: lift RAG to Azure AI Search | first cloud resource (managed search) |
| v0.3 | M3: agent fetches its own StatCan data | API tool, orchestration |
| v0.4 | M4: memory + database (follow-ups) | SQL, caching, agent memory |
| v0.5 | M5: evaluator ("critic") agent | multi-agent, LLM-as-judge |
| v1.0 | Hardened deploy + README | Docker, Terraform, CI/CD, endpoint, monitoring |
| *(optional)* | Quality-flag classifier | train a model → deploy as an endpoint |

**Trust the steps, not a calendar.** You always have a working, deployed thing to show.

---

## Cloud (how it enters)

Cloud is table-stakes on nearly all your JDs — Azure-primary for your set. You don't learn it as a separate course; it enters **through the features that need it**: managed search at v0.2b (free tier), then the deploy-heavy stack at v1.0 (Docker, Terraform, CI/CD, endpoint, monitoring), and optionally a trained classifier endpoint.

Your HPC/Slurm background already covers most of the concepts (remote/distributed compute, jobs, environments, resource limits). The new ~25–30%: *you* own provisioning, *you* own the cost, and you can rent **finished managed services**. One rule that has no Slurm parallel: **the cloud meter runs as long as a resource exists, not just while it computes** — stay on free tiers, and delete any paid service the day you test it.

---

## Deliberately off the roadmap

- **Fine-tuning.** RAG + tool use + deterministic validation is the right pattern for regularly-updated live data; fine-tuning bakes in stale numbers and turns an explainable moat into a black box. "Considered and consciously skipped" is the stronger answer. *(A small supervised classifier is a different thing — that's the honest way to show "train a model.")*
- **Big-data Spark/Databricks.** Your data scale doesn't justify it; forcing it reads as resume-driven. Skip until scale demands it.

---

## Guardrails to design (your health expertise = the moat)

- Agent invents a column / wrong dataset → ground it against real columns.
- Code errors → retry-on-error loop.
- Misreads a definition → RAG grounding + citation.
- Cites a source that doesn't support the claim → no definitional claim without a supporting retrieved chunk.
- Operates on wrongly-shaped data → remember correctness ≠ quality ≠ grounding.
- Over-claims causation from correlational data → safe framing.
- `exec` runs LLM code → fine locally on trusted data; keep the public showcase static/API-free; sandbox before any live public exec.

---

## Mentor checkpoints

- **Bhaskar / Sahib:** bring a *specific* question, not "am I doing okay?" — e.g. "how would you structure the agent's self-correction loop?", "how do I test that a citation actually supports a claim?", "where's the line between free-tier-safe experimentation and a service that quietly bills me?"

---

## One-line compass

Build MapleVitals one feature at a time. Each week: learn one thing (≤3 hrs), then ship the next version. When lost, open the repo. Deploy early, post as you go, let cloud enter through the features that need it, and lean on the health judgment only you have.
