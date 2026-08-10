from pathlib import Path

from docx import Document

from backend.app.services.docx import convert_tex_to_docx

RESUME_TEX = r"""
\documentclass{article}
\newcommand{\resumeItem}[1]{\item #1}
\newcommand{\resumeSubheading}[4]{\item \textbf{#1} \\ \textit{#2} \\ #3 -- #4}
\newcommand{\resumeProject}[2]{\item[] \textbf{#1} \\ \textit{#2}}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\begin{document}
\begin{center}
{\Huge \textbf{Test Candidate}} \\
test@example.com
\end{center}
\section{EXPERIENCE}
\resumeSubHeadingListStart
\resumeSubheading{Example Corp}{Software Engineer}{Jan 2020}{Present}
\resumeItemListStart
\resumeItem{Built things.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\section{PROJECTS}
\resumeSubHeadingListStart
\resumeProject{Sample Project}{Python, FastAPI}
\resumeItemListStart
\resumeItem{Did project work.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\end{document}
"""


def test_docx_project_has_no_date_range(tmp_path: Path):
    """Projects intentionally have no date range (unlike Experience/Education):
    \\resumeProject{title}{tech stack} only takes 2 arguments, and the DOCX
    output must render just the title + tech stack with no stray date text."""
    tex_path = tmp_path / "resume.tex"
    tex_path.write_text(RESUME_TEX, encoding="utf-8")
    out_path = tmp_path / "resume.docx"

    convert_tex_to_docx(tex_path, out_path)

    doc = Document(str(out_path))
    project_line = next(p.text for p in doc.paragraphs if "Sample Project" in p.text)
    assert project_line == "Sample Project | Python, FastAPI"

    experience_line = next(p.text for p in doc.paragraphs if "Example Corp" in p.text)
    assert "Jan 2020" in experience_line
    assert "Present" in experience_line
