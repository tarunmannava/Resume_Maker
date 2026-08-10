# AI project interview guide (student / lab framing)

Use this when explaining portfolio projects on the AI Engineer resume. Each project sits in the same problem space as **USF SHIELD Lab**: AI features used by **students and instructors** in a biomedical learning platform — not a fictional enterprise platform team.

---

## The arc (tell this in order, oldest → newest)

1. **RAG** — Can we answer questions grounded in course/lab material?
2. **Multi-Agent** — Can we automate multi-step research workflows?
3. **Prompt Registry** — Can we version and test prompts safely across modules?
4. **LLM Infrastructure** — Can we host models for classroom load without relying only on APIs?

Your **USF experience** is the real production anchor. Projects show how you'd extend that stack as a graduate student building capstone depth.

---

## Project 1 — Hybrid RAG Support Assistant

**Dates:** Jan 2025 – Apr 2025

**Use case:** Students ask questions about course readings, lab procedures, and module content. A plain LLM hallucinates; RAG grounds answers in indexed documents.

**What you built:** Hybrid retrieval (BM25 + vectors + reranking), evaluation before shipping, FastAPI service for tutoring modules.

**30-second answer:**

> "I built a RAG assistant over course and lab documentation so tutoring features could answer from verified material, not model memory. I combined sparse and dense retrieval with reranking, evaluated on golden Q&A from course content, and exposed it as a FastAPI service that could plug into the same kind of student-facing modules I work on at USF."

**If they ask "who used it?"**

> "Portfolio capstone aligned with my graduate AI work — designed for the same student/instructor tutoring context as the SHIELD Lab platform, with offline eval gates before any live rollout."

---

## Project 2 — Multi-Agent Research Platform

**Dates:** May 2025 – Aug 2025

**Use case:** Graduate research involves repetitive multi-step work — find papers, summarize, structure notes. Agents decompose that into tool-backed steps with guardrails.

**What you built:** LangGraph orchestration, JSON tool schemas, retries/timeouts/token limits, persisted state for long runs.

**30-second answer:**

> "I built a LangGraph multi-agent system for graduate research workflows like literature search and structured summarization. Agents decompose tasks in parallel, call tools through strict JSON schemas, and hit guardrails so runs don't loop forever. State lives in Postgres with Redis caching so a failed API call doesn't throw away an hour of work."

**LangGraph timing:** Public release Jan 2024 — using it in Summer 2025 as an MS student is credible.

---

## Project 3 — Prompt Registry & Experimentation

**Dates:** Sep 2025 – Dec 2025

**Use case:** The platform has many AI touchpoints (tutoring hints, quiz feedback, instructor tools). Hard-coding prompts in repos doesn't scale; you need versioning, A/B tests, and safe rollouts during live classes.

**What you built:** Central registry, OpenAI vs Gemini experiments on educational prompts, canary routing, Grafana for cost/latency during peak lab hours.

**30-second answer:**

> "Different learning modules need different prompts, and we iterate during the semester. I built a prompt registry with versioning and rollback, A/B tests for tutoring and quiz-feedback prompts across OpenAI and Gemini, and canary routing so we can update prompts without redeploying the whole app during live class."

**Connect to USF:**

> "Same shape of problem as managing prompts across 13 platform modules — this project isolates that as a reusable service."

---

## Project 4 — LLM Infrastructure & MLOps

**Dates:** Jan 2026 – Apr 2026

**Use case:** At USF you use Groq/APIs for live classes. A capstone infra project asks: *what if we self-host open models for classroom-scale load, cost control, and learning the ops side?*

**What you built:** vLLM on Kubernetes with GPU autoscaling, Terraform + GitHub Actions for staging clusters, Prometheus/Grafana for GPU and queue health during simulated lab sessions.

**30-second answer:**

> "My USF platform runs on Groq today. For my infra capstone I built the self-hosted path: vLLM on Kubernetes with GPU autoscaling for classroom-concurrent tutoring load, Terraform and GitHub Actions to spin up staging clusters quickly, and Prometheus/Grafana to see when GPUs or request queues cause slow responses during peak lab usage."

**If they ask "was this production?"**

> "Capstone / portfolio deployment targeting the same 60+ concurrent student load class I support at the lab — load-tested staging environment, not claiming enterprise SLA."

**What each bullet maps to:**

| Bullet | Student pain |
|--------|----------------|
| vLLM + K8s autoscaling | Whole class opens AI tutor at once |
| Terraform + Actions | Test new model before pointing students at it |
| Prometheus + Grafana | "Why is the tutor slow?" during live session |

---

## Phrases to use vs avoid

| Use | Avoid |
|-----|--------|
| Classroom-scale / lab-session traffic | 99.9% production uptime |
| 13+ learning modules / students & instructors | 40+ production AI applications |
| Capstone / portfolio / aligned with USF work | Internal platform team at Fortune 500 |
| Held-out student FAQ eval | Production query categories at scale |
| Staging cluster / load test | 10x enterprise traffic spikes (unless measured) |

---

## Tie-back to USF experience (strong close)

> "My USF role is shipping real AI features for students and instructors — Groq integration, 13 modules, live classroom usage. These projects show the surrounding skills: grounded retrieval, agent orchestration, prompt lifecycle, and self-hosted inference — all in the same educational context, not random enterprise fiction."
