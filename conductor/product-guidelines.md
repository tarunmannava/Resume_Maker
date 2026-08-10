# Product Guidelines: Resume Maker

## Voice and Tone
- **Professional & Tier-1 Engineering Standard**: Bullet rewrites must reflect senior production-engineering rigor (e.g. built, designed, optimized, scaled) and eliminate generic buzzwords.
- **Defensible & Quantifiable**: All resume modifications must maintain truthfulness to the candidate's core accomplishments while embedding verifiable metrics (% throughput, latency bounds, volume, scale).

## UX & Content Principles
- **No Deletion of Core History**: The candidate's original employment timeline, employers, dates, and education must remain completely intact.
- **ATS Compliance First**: Strictly enforce clean text, avoid non-standard LaTeX packages or markdown fences, and preserve original pipe separators (`|`).
- **Deterministic Guardrails**: LLMs are augmented with post-processing guards to prevent hallucinated projects, unsupported skill claims, or malformed LaTeX syntax.
