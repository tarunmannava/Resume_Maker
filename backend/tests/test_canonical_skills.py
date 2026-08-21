import pytest
from backend.app.services.skills_data import SKILLS_TEMPLATES, get_skills_template_for_stack


def test_skills_templates_loaded():
    assert "dotnet" in SKILLS_TEMPLATES
    assert "java" in SKILLS_TEMPLATES
    assert "ai" in SKILLS_TEMPLATES
    assert "python" in SKILLS_TEMPLATES
    assert "node" in SKILLS_TEMPLATES


def test_get_skills_template_for_stack():
    dotnet_tmpl = get_skills_template_for_stack("dotnet")
    assert dotnet_tmpl is not None
    assert dotnet_tmpl["name"] == ".NET / C# Developer"
    assert "\\textbf{Languages \\& Core:}" in dotnet_tmpl["raw_latex"]

    java_tmpl = get_skills_template_for_stack("java")
    assert java_tmpl is not None
    assert java_tmpl["name"] == "Java Developer"
    assert "\\textbf{Backend \\& Frameworks:}" in java_tmpl["raw_latex"]

    ai_tmpl = get_skills_template_for_stack("ai")
    assert ai_tmpl is not None
    assert ai_tmpl["name"] == "AI Engineer"
    assert "\\textbf{GenAI \\& LLM Frameworks:}" in ai_tmpl["raw_latex"]

    python_tmpl = get_skills_template_for_stack("python")
    assert python_tmpl is not None
    assert python_tmpl["name"] == "Python Developer"

    node_tmpl = get_skills_template_for_stack("node")
    assert node_tmpl is not None
    assert node_tmpl["name"] == "Node.js / Fullstack"


def test_inject_canonical_skills_section_dotnet():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "dotnet")
    assert "C\\#, .NET 8 / .NET Core, ASP.NET Core" in injected
    assert "RabbitMQ, Redis Caching, OAuth2, Azure AD" in injected


def test_inject_canonical_skills_section_java():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "java")
    assert "Spring Boot, Spring MVC, Spring Security" in injected
    assert "RabbitMQ, Redis, CompletableFuture" in injected


def test_inject_canonical_skills_section_ai():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "ai")
    assert "LangChain, LlamaIndex, LangGraph" in injected
    assert "RabbitMQ" in injected


def test_inject_canonical_skills_section_python():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "python")
    assert "\\textbf{Backend \\& APIs:} FastAPI, Flask, Django" in injected


def test_inject_canonical_skills_section_node():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "node")
    assert "TypeScript, JavaScript" in injected
    assert "\\textbf{Backend \\& APIs:} Node.js, Express.js" in injected


def test_inject_canonical_skills_section_banned_skills():
    from backend.app.services.latex_skills import inject_canonical_skills_section

    doc = "\\begin{document}\n\\section{EXPERIENCE}\n\\end{document}"
    injected = inject_canonical_skills_section(doc, "java", banned_skills=["Hibernate", "Kafka"])
    assert "Hibernate" not in injected
    assert "Spring Boot" in injected
    assert "Java (11/17/21)" in injected
