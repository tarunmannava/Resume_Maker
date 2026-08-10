# Product Definition: Resume Maker (v2)

## Vision
Resume Maker is an AI-powered, ATS-focused LaTeX resume rewriting and optimization engine. It enables candidates to tailor their professional LaTeX resumes for target job descriptions with high technical accuracy, defensible accomplishments, role-specific project injection, and automated PDF compilation.

## Key Features
- **ATS Keyword Extraction & Scoring**: Evaluates keyword overlap, weights, required vs preferred requirements, and risk levels (e.g., C/C++ or Kubernetes high-risk substitutions).
- **Target Role & Industry Alignment**: Classifies role identity (e.g. Backend, ML, Fullstack, AI Platform Engineer) and detects target industry (Fintech, Healthcare, E-commerce, Cybersecurity, EdTech) to contextualize metrics and technical framing.
- **Deterministic & RAG-driven Project Reframing**: Dynamically selects and injects 2 relevant, industry-framed technical projects into the candidate's resume while suppressing out-of-domain jargon.
- **FAANG/Tier-1 Action-Oriented Bullet Rewriting**: Transforms generic statements into metric-backed (X-Y-Z formula: Accomplished [X] measured by [Y] doing [Z]), technology-dense bullet points.
- **LaTeX Preservation & PDF Compilation**: Strictly preserves existing LaTeX document macros, formatting, and pipe separators (`|`), and compiles output directly to production-grade PDF.
- **Screening Question Assistance**: Provides context-aware answers to application screening questions based on the candidate's resume and job target.
