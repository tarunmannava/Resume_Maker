import pytest
from pathlib import Path
from backend.app.services.rewrite import (
    get_archetype_latex,
    enforce_section_order_for_stack,
    remove_inline_bolding_from_bullets,
)
from backend.app.services.latex_skills import enforce_reverse_chronological_experience
from backend.app.services.docx import convert_tex_to_docx

STACKS = ["ai", "node", "java", "dotnet", "python"]


def test_all_five_archetypes_exist_and_load():
    for stack in STACKS:
        latex = get_archetype_latex(stack)
        assert latex is not None, f"Archetype for stack '{stack}' failed to load."
        assert len(latex) > 1000, f"Archetype for stack '{stack}' is suspiciously short."


def test_section_ordering_per_archetype():
    for stack in STACKS:
        latex = get_archetype_latex(stack)
        ordered_latex = enforce_section_order_for_stack(latex, stack)

        proj_idx = ordered_latex.find(r"\section{PROJECTS}")
        if proj_idx == -1:
            proj_idx = ordered_latex.find(r"\section{Projects}")

        exp_idx = ordered_latex.find(r"\section{EXPERIENCE}")
        if exp_idx == -1:
            exp_idx = ordered_latex.find(r"\section{Experience}")

        assert proj_idx != -1, f"Projects section missing in stack '{stack}'"
        assert exp_idx != -1, f"Experience section missing in stack '{stack}'"

        if stack == "ai":
            assert proj_idx < exp_idx, (
                f"For stack 'ai', PROJECTS must come BEFORE EXPERIENCE. "
                f"Got proj_idx={proj_idx}, exp_idx={exp_idx}"
            )
        else:
            assert exp_idx < proj_idx, (
                f"For stack '{stack}', EXPERIENCE must come BEFORE PROJECTS. "
                f"Got exp_idx={exp_idx}, proj_idx={proj_idx}"
            )


def test_experience_reverse_chronology():
    for stack in STACKS:
        latex = get_archetype_latex(stack)
        latex = enforce_reverse_chronological_experience(latex)

        usf_idx = latex.find("University of South Florida")
        cog_idx = latex.find("Cognizant Technology Solutions")

        assert usf_idx != -1, f"USF missing in {stack}"
        assert cog_idx != -1, f"Cognizant missing in {stack}"
        assert usf_idx < cog_idx, f"USF must come before Cognizant in {stack}"


def test_zero_inline_bolding_in_bullets():
    for stack in STACKS:
        latex = get_archetype_latex(stack)
        cleaned = remove_inline_bolding_from_bullets(latex)
        # Check all resumeItem lines for \textbf{
        for line in cleaned.splitlines():
            if r"\resumeItem" in line:
                assert r"\textbf{" not in line, f"Found inline bolding in {stack} bullet: {line}"


def test_all_five_archetypes_compile_to_docx(tmp_path):
    for stack in STACKS:
        latex = get_archetype_latex(stack)
        tex_path = tmp_path / f"{stack}.tex"
        docx_path = tmp_path / f"{stack}.docx"
        tex_path.write_text(latex, encoding="utf-8")
        convert_tex_to_docx(tex_path, docx_path)

        assert docx_path.exists(), f"DOCX failed to compile for {stack}"
        assert docx_path.stat().st_size > 5000, f"DOCX for {stack} is suspiciously small ({docx_path.stat().st_size} bytes)"


def test_rewrite_resume_archetype_routing_all_stacks(monkeypatch, tmp_path):
    from backend.app.models.schemas import RewriteRequest
    from backend.app.services.rewrite import rewrite_resume

    # Generic base resume with Tarun Mannava
    tarun_generic_base = r"""
\documentclass[a4paper,10pt]{article}
\begin{document}
\textbf{\Huge Tarun Mannava}
\section{EXPERIENCE}
\section{PROJECTS}
\section{SKILLS}
\end{document}
"""

    # Mock the LLM call to echo back whatever prompt-provided latex it received
    def mock_generate_rewrite(prompt, align_titles=False):
        # Extract the source latex block from the prompt
        marker = "SOURCE LATEX RESUME TO REWRITE:\n"
        idx = prompt.find(marker)
        if idx != -1:
            end_marker = "\nPlease output the complete"
            end_idx = prompt.find(end_marker, idx)
            source_tex = prompt[idx + len(marker):end_idx].strip()
            return (source_tex, "mock_llm", None)
        return (tarun_generic_base, "mock_llm", None)

    monkeypatch.setattr("backend.app.services.rewrite.generate_rewrite", mock_generate_rewrite)

    jd_map = {
        "ai": "Senior AI Engineer with LangGraph, MCP, RAG, and LLM evaluation experience.",
        "node": "Full Stack Node.js Engineer with TypeScript, React, Next.js, and Express.",
        "java": "Senior Java Developer with Spring Boot, Microservices, and PostgreSQL.",
        "dotnet": "Senior .NET Developer with C#, ASP.NET Core, and Entity Framework.",
        "python": "Backend Python Developer with FastAPI, SQLAlchemy, and AsyncIO.",
    }

    for stack, jd in jd_map.items():
        req = RewriteRequest(
            job_description=jd,
            resume_latex=tarun_generic_base,
            target_stack=stack,
        )
        res = rewrite_resume(req)
        rewritten = res.rewritten_latex

        # 1. Reverse Chronology in Experience
        usf_idx = rewritten.find("University of South Florida")
        cog_idx = rewritten.find("Cognizant Technology Solutions")
        assert usf_idx != -1 and cog_idx != -1, f"Missing USF or Cognizant in {stack}"
        assert usf_idx < cog_idx, f"USF must precede Cognizant in {stack}"

        # 3. Section Order
        proj_idx = rewritten.find(r"\section{PROJECTS}")
        if proj_idx == -1:
            proj_idx = rewritten.find(r"\section{Projects}")
        exp_idx = rewritten.find(r"\section{EXPERIENCE}")
        if exp_idx == -1:
            exp_idx = rewritten.find(r"\section{Experience}")

        if stack == "ai":
            assert proj_idx < exp_idx, f"PROJECTS must precede EXPERIENCE for {stack}"
        else:
            assert exp_idx < proj_idx, f"EXPERIENCE must precede PROJECTS for {stack}"

        # 4. DOCX compiles cleanly
        docx_path = tmp_path / f"rewritten_{stack}.docx"
        tex_path = tmp_path / f"rewritten_{stack}.tex"
        tex_path.write_text(rewritten, encoding="utf-8")
        convert_tex_to_docx(tex_path, docx_path)
        assert docx_path.exists(), f"DOCX generation failed for rewritten {stack}"
        assert docx_path.stat().st_size > 5000


def test_all_five_archetypes_have_summary_in_header():
    """All 5 archetypes must have their canonical summary in the centered header."""
    for stack in STACKS:
        latex = get_archetype_latex(stack)
        assert r"\begin{center}" in latex
        assert r"\textit{" in latex
        assert "years of experience" in latex or "experience" in latex
        # There should NOT be an orphan \section{SUMMARY} in the archetype
        assert r"\section{SUMMARY}" not in latex
        assert r"\section{Summary}" not in latex


def test_normalize_summary_placement():
    from backend.app.services.rewrite import normalize_summary_placement

    # Case 1: \section{SUMMARY} in body should be extracted and moved to \begin{center}
    tex_with_sec = r"""\documentclass{article}\begin{document}
\begin{center}
{\Huge \textbf{Tarun Mannava}} \\[2pt]
\textbf{AI Engineer} \\[4pt]
\small
\resumeHeadingContact
\end{center}
\vspace{-10pt}
\section{SUMMARY}
Custom extracted AI summary with 4+ years of experience in LLMs.
\section{SKILLS}
\end{document}"""
    norm1 = normalize_summary_placement(tex_with_sec, "ai")
    assert r"\section{SUMMARY}" not in norm1
    assert r"\textit{Custom extracted AI summary with 4+ years of experience in LLMs.}" in norm1

    # Case 2: No summary in \begin{center} should have canonical stack summary injected
    tex_no_summary = r"""\documentclass{article}\begin{document}
\begin{center}
{\Huge \textbf{Tarun Mannava}} \\[2pt]
\textbf{Full Stack Software Engineer} \\[4pt]
\small
\resumeHeadingContact
\end{center}
\vspace{-10pt}
\section{SKILLS}
\end{document}"""
    norm2 = normalize_summary_placement(tex_no_summary, "node")
    assert r"\textit{" in norm2
    assert "AWS Bedrock" in norm2 or "Node.js" in norm2

