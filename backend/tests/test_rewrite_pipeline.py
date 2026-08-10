"""End-to-end tests for the rewrite pipeline with the LLM call mocked out."""

from backend.app.models.schemas import RewriteRequest
from backend.app.services import rewrite as rewrite_service

SAMPLE_RESUME = r"""
\documentclass{article}
\newcommand{\resumeItem}[1]{\item #1}
\newcommand{\resumeSubheading}[4]{\item \textbf{#1} \\ \textit{#2} \\ #3 -- #4}
\newcommand{\resumeProject}[2]{\item[] \textbf{#1} \\ \textit{#2}}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\begin{document}
\section{EXPERIENCE}
\resumeSubHeadingListStart
\resumeSubheading{Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
\resumeItemListStart
\resumeItem{Developed Java Spring Boot REST APIs with PostgreSQL and Redis.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\section{PROJECTS}
\resumeSubHeadingListStart
\resumeProject{Sample Project}{Python}
\resumeItemListStart
\resumeItem{Built a sample project.}
\resumeItemListEnd
\resumeSubHeadingListEnd
\section{SKILLS}
\begin{itemize}
\item Java, Spring Boot, PostgreSQL, Redis, Kafka
\end{itemize}
\end{document}
"""

JOB_DESCRIPTION = (
    "We are hiring a Backend Software Engineer with Java, Spring Boot, REST APIs, "
    "PostgreSQL, and Redis experience to build scalable microservices."
)

COMPLETE_OUTPUT = SAMPLE_RESUME.replace("Sample Project", "Rewritten Project")


def _request(**overrides) -> RewriteRequest:
    defaults = dict(
        job_description=JOB_DESCRIPTION,
        resume_latex=SAMPLE_RESUME,
        rewrite_mode="transferable",
    )
    defaults.update(overrides)
    return RewriteRequest(**defaults)


def test_rewrite_resume_end_to_end_smoke(monkeypatch):
    """Basic JD -> relevant projects -> rewritten LaTeX flow must complete
    without raising, and return a non-empty, well-formed rewritten resume."""
    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (COMPLETE_OUTPUT, "test", None),
    )

    response = rewrite_service.rewrite_resume(_request())

    assert response.rewritten_latex.strip().endswith(r"\end{document}")
    assert r"\section{PROJECTS}" in response.rewritten_latex
    assert response.match_score >= 0


def test_rewrite_resume_requests_continuation_when_output_truncated(monkeypatch):
    """If the model's output is cut off before \\end{document}, the pipeline
    should repair the document so it is well-formed."""
    truncated = COMPLETE_OUTPUT[: COMPLETE_OUTPUT.index(r"\end{document}")]

    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (truncated, "test", None),
    )

    response = rewrite_service.rewrite_resume(_request())

    assert response.rewritten_latex.strip().endswith(r"\end{document}")


def test_rewrite_resume_removes_banned_skills(monkeypatch):
    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (COMPLETE_OUTPUT, "test", None),
    )

    response = rewrite_service.rewrite_resume(_request(banned_skills=["Kafka"]))

    assert "Kafka" not in response.rewritten_latex


def test_rewrite_resume_handles_no_content_from_provider(monkeypatch):
    monkeypatch.setattr(
        rewrite_service,
        "generate_rewrite",
        lambda prompt, align_titles=False: (None, "test", "simulated failure"),
    )

    response = rewrite_service.rewrite_resume(_request())

    assert response.rewritten_latex == SAMPLE_RESUME
    assert any("simulated failure" in w for w in response.warnings)


def test_generate_with_openai_handles_empty_choices(monkeypatch):
    class FakeCompletion:
        choices: list = []

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeCompletion()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(rewrite_service, "OpenAI", lambda **kwargs: FakeClient())
    monkeypatch.setattr(
        rewrite_service,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "openai_api_key": "fake",
                "openrouter_api_key": None,
                "openai_base_url": None,
                "openai_model": "fake-model",
                "max_output_tokens": 1000,
            },
        )(),
    )

    content, error = rewrite_service.generate_with_openai("prompt")
    assert content is None
    assert error is not None
