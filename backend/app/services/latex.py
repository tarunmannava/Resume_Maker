import re

SECTION_PATTERNS = [
    "education",
    "experience",
    "work experience",
    "projects",
    "skills",
    "technical skills",
    "certifications",
    "summary",
]


def latex_to_text(latex: str) -> str:
    """Best-effort conversion of resume LaTeX to plain text for keyword analysis."""
    text = latex
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\\(href|url)\{([^{}]*)\}\{([^{}]*)\}", r"\2 \3", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("\\&", "&")
    text = text.replace("\\%", "%")
    text = text.replace("\\_", "_")
    text = text.replace("~", " ")
    text = re.sub(r"[{}$^]", " ", text)
    text = re.sub(r"\\.", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_sections(latex: str) -> list[str]:
    lowered = latex_to_text(latex).lower()
    found: list[str] = []
    for section in SECTION_PATTERNS:
        if section in lowered:
            found.append(section)
    return sorted(set(found))


def ats_warnings(latex: str) -> list[str]:
    warnings: list[str] = []
    risky_patterns = {
        "tabular": "Tables can parse poorly in ATS systems.",
        "multicols": "Multi-column layouts can confuse ATS text extraction.",
        "includegraphics": "Images/icons are usually not ATS-readable.",
        "fontawesome": "Icon fonts may not be read correctly by ATS systems.",
        "tikzpicture": "Graphics-based layout can break ATS parsing.",
        "textcolor": "Colored or hidden text can reduce ATS reliability.",
    }
    lowered = latex.lower()
    for pattern, message in risky_patterns.items():
        if pattern in lowered:
            warnings.append(message)
    if "\\section" not in latex and "resumeSubHeading" not in latex:
        warnings.append(
            "No obvious standard section commands found; verify the template extracts clean text."
        )
    return warnings
