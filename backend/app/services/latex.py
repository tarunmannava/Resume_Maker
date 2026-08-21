import re
import logging

logger = logging.getLogger("uvicorn.error")

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


def _extract_brace_arg(text: str, pos: int) -> tuple[str, int]:
    """Extract a balanced {…} argument starting at pos. Returns (content, end_pos)."""
    if pos >= len(text) or text[pos] != "{":
        return "", pos
    depth = 0
    start = pos + 1
    i = pos
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2  # skip escaped char
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    # Unbalanced — return what we have
    return text[start:], len(text)


def _replace_macro(text: str, macro_name: str, num_args: int, formatter) -> str:
    """Replace \\macroName{arg1}{arg2}... with formatter([arg1, arg2, ...])."""
    pattern = "\\" + macro_name
    result = []
    i = 0
    while i < len(text):
        idx = text.find(pattern, i)
        if idx == -1:
            result.append(text[i:])
            break
        result.append(text[i:idx])
        pos = idx + len(pattern)
        # Skip optional whitespace between macro name and first {
        while pos < len(text) and text[pos] in " \t\n\r":
            pos += 1
        args = []
        for _ in range(num_args):
            while pos < len(text) and text[pos] in " \t\n\r":
                pos += 1
            arg, pos = _extract_brace_arg(text, pos)
            args.append(arg)
        if len(args) == num_args:
            result.append(formatter(args))
        else:
            # Couldn't parse all args, keep original text
            result.append(text[idx:pos])
        i = pos
    return "".join(result)


def latex_to_text(latex: str) -> str:
    """Cleanly converts resume LaTeX to structured plain text for keyword & ATS analysis."""
    text = latex

    # 1. Extract only the body between \begin{document} and \end{document} to discard preamble/macros
    if r"\begin{document}" in text:
        text = text[text.find(r"\begin{document}") + len(r"\begin{document}") :]
    if r"\end{document}" in text:
        text = text[: text.find(r"\end{document}")]

    # 2. Protect escaped characters
    text = text.replace(r"\%", "%")
    text = text.replace(r"\&", "&")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\#", "#")
    text = text.replace(r"\$", "$")

    # 3. Strip LaTeX comments line by line
    cleaned_lines = []
    for line in text.splitlines():
        line_strip = line.strip()
        if line_strip.startswith("%"):
            continue
        comment_idx = line.find("%")
        if comment_idx != -1:
            line = line[:comment_idx]
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    # 4. Convert custom resume macros into readable structured text
    # Use balanced-brace extraction for nested content
    text = _replace_macro(text, "resumeSubheading", 4, lambda args: f"\n\n{args[0]} | {args[1]} | {args[2]} - {args[3]}\n")
    text = _replace_macro(text, "resumeProject", 2, lambda args: f"\n\n{args[0]} ({args[1]})\n")
    text = _replace_macro(text, "resumeItem", 1, lambda args: f"\n* {args[0]}")

    # Convert sections \section{EXPERIENCE} -> \n\n=== EXPERIENCE ===\n
    text = re.sub(r"\\section\*?\s*\{([^}]*)\}", r"\n\n=== \1 ===\n", text)

    # Extract href and url links content: \href{url}{label} -> label
    text = re.sub(r"\\(href|url)\{([^{}]*)\}\{([^{}]*)\}", r"\3", text)

    # Strip inline styling macros while preserving content: \textbf{abc} -> abc, \textit{abc} -> abc
    for _ in range(5):
        text = re.sub(r"\\[a-zA-Z]+\*?\{([^{}]*)\}", r"\1", text)

    # Replace any leftover LaTeX commands \command with space
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", text)

    # Replace formatting symbols
    text = text.replace("~", " ")
    text = text.replace(r"\\", "\n")
    text = re.sub(r"[{}\$^]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
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


def sanitize_latex_escaping(latex: str) -> str:
    """Sanitizes unescaped special LaTeX characters while preserving LaTeX commands.
    Only operates on the document body to avoid corrupting preamble macro comments."""
    begin_marker = r"\begin{document}"
    if begin_marker in latex:
        split_idx = latex.find(begin_marker) + len(begin_marker)
        preamble_part = latex[:split_idx]
        body_part = latex[split_idx:]
    else:
        preamble_part = ""
        body_part = latex

    sanitized_lines = []
    for line in body_part.splitlines():
        if line.strip().startswith("%"):
            sanitized_lines.append(line)
            continue
        sanitized = re.sub(r"(?<!\\)%", r"\%", line)
        sanitized_lines.append(sanitized)

    return preamble_part + "\n".join(sanitized_lines)
