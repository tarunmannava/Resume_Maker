import pytest
from backend.app.services.skills_data import SKILLS_TEMPLATES, get_skills_template_for_stack


def test_skills_templates_loaded():
    assert "java" in SKILLS_TEMPLATES
    assert "ai" in SKILLS_TEMPLATES
    assert "python" in SKILLS_TEMPLATES
    assert "node" in SKILLS_TEMPLATES


def test_get_skills_template_for_stack():
    java_tmpl = get_skills_template_for_stack("java")
    assert java_tmpl is not None
    assert java_tmpl["name"] == "Java Developer"
    assert "\\textbf{Backend:}" in java_tmpl["raw_latex"]

    ai_tmpl = get_skills_template_for_stack("ai")
    assert ai_tmpl is not None
    assert ai_tmpl["name"] == "AI Engineer"
    assert "\\textbf{LLM APIs:}" in ai_tmpl["raw_latex"]

    python_tmpl = get_skills_template_for_stack("python")
    assert python_tmpl is not None
    assert python_tmpl["name"] == "Python Developer"

    node_tmpl = get_skills_template_for_stack("node")
    assert node_tmpl is not None
    assert node_tmpl["name"] == "Node.js / Fullstack"


def test_inject_canonical_skills_section_java():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "java")
    assert "\\textbf{Backend:} Java, Spring Boot" in injected
    assert "\\textbf{Concurrency:} CompletableFuture" in injected


def test_inject_canonical_skills_section_ai():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "ai")
    assert "\\textbf{LLM APIs:} OpenAI, Anthropic, Groq, Gemini" in injected
    assert "\\textbf{AI \\& ML:} LangChain, LlamaIndex, LangGraph" in injected


def test_inject_canonical_skills_section_python():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "python")
    assert "\\textbf{Backend:} FastAPI, Flask, Pydantic" in injected


def test_inject_canonical_skills_section_node():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "node")
    assert "\\textbf{Core:} TypeScript, Node.js" in injected
    assert "\\textbf{Backend \\& APIs:} Express.js" in injected


def test_inject_canonical_skills_section_banned_skills():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "java", banned_skills=["Hibernate", "Kafka"])
    assert "Hibernate" not in injected
    assert "Java, Spring Boot" in injected
