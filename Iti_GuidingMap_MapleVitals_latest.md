# MapleVitals — Guiding Map

*A Canadian public-health agent platform, built one feature at a time.*

**For:** Iti · **Pace:** ~8–10 hrs/week · **Approach:** ship small and public, learn on the go.

---

## You are here

- ✅ **M0 done** — script loads StatCan data, Claude describes it.
- 🔨 **M1 in progress** — agent turns a question into a chart + interpretation.
- ⏭ **Next after M1:** deploy it. That live link = **LinkedIn post #1.**

---

## The 3 rules

1. **Build, don't binge.** Cap learning at ~3 hrs/week; spend the rest hands-on-keyboard.
2. **One product, one repo, forever.** Every new skill is a *feature added*, not a new project.
3. **When lost, open the repo** — not another tutorial. Make the current "Done when" true.

---

## The product

Ask a Canadian health question in plain English → MapleVitals writes the analysis, runs it, returns a chart + a short interpretation grounded in the real source.

**Your edge:** your epidemiology background lets you judge when the output is *wrong* — most builders can't. That's your story.

---

## How you'll work now (the pivot)

**Deploy first, then stack features.** Each feature = a version bump = one **build-log** LinkedIn post.

But posting isn't gated on shipping. Build-log version posts are only **one of four content pillars** (build log · health insight · AI concept · opinion). The health, AI, and opinion posts fill the weeks between releases — that's how you sustain ~1–2 posts/week even when no new version is out. **The tracker is the source of truth for what to post next;** this doc just sets the build direction.

You don't need to understand everything. For **each piece**, be able to explain three things:
1. **What** does it do?
2. **How**, roughly? (what the agent calls, the flow)
3. **Where** does it break — and what guardrail did you add?

Go deep on the **agent loop + guardrails**. Skip the boilerplate (pandas, Streamlit plumbing). Let Claude write the code; you own the design, the guardrails, and the health-data judgment.

---

## The roadmap

Each is one feature, one version, one post. Order can flex.

| Version | Feature | The new skill |
|---|---|---|
| ✅ — | M0: data → LLM description | LLM API calls |
| 🔨 v0.1 | M1: question → chart + interpretation | agent loop, tool calling |
| ⏭ v0.1‑live | **Deploy M1 (Streamlit)** → post #1 | deployment, secrets, cost guardrails |
| v0.2 | RAG grounding + citations | embeddings, vector DB |
| v0.3 | Agent fetches its own StatCan data | API tool, orchestration |
| v0.4 | Memory + database (follow-up questions) | SQL, caching, agent memory |
| v0.5 | Evaluator ("critic") agent | multi-agent, LLM-as-judge |
| v1.0 | Hardened deploy + README | FastAPI/Docker, LLMOps |

*Each version bump above = one build-log "version update" post. But that's only a fraction of your 50 — most posts come from the health-insight, AI-concept, and opinion pillars, which don't depend on shipping. See the tracker for the full mix.*

**Trust the steps, not a calendar.** A slow start is fine — the words are new, not the work. You always have a *working, deployed* thing to show.

---

## Guardrails to design (your health expertise = the moat)

- Agent invents a column / wrong dataset → ground it, validate against real columns.
- Code errors → retry-on-error loop.
- Misreads a definition (e.g. age-standardized rate) → surface metadata.
- Over-claims causation from correlational data → safe framing.
- `exec` runs LLM code → fine locally; sandbox before public.

---

## Mentor checkpoints

- **Bhaskarjit / Sahib:** bring a *specific* question (e.g. "how would you structure the agent's self-correction loop?"), not "am I doing okay?"

---

## One-line compass

Build MapleVitals one feature at a time. Each week: learn one thing (≤3 hrs), then ship the next version. When lost, open the repo. Deploy early, post as you go, and lean on the health judgment only you have.

**Next move:** finish M1, then deploy it as post #1.
