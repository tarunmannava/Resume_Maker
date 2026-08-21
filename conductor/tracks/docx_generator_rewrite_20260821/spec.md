# Specification: DOCX Generator Complete Rewrite

## 1. Overview
Complete architectural rewrite of `backend/app/services/docx.py` into a token/tree-based LaTeX converter that generates clean, pixel-perfect, ATS-compliant Microsoft Word (`.docx`) documents from resume LaTeX.

## 2. Functional Requirements
- **Contact Header & Metadata:**
  - Centered candidate name (18pt, bold, Times New Roman).
  - Contact details cleanly separated by bullet glyphs (`Seattle, WA • +1 (656) 203-7074 • mannava.tarun34@gmail.com • LinkedIn • GitHub`).
  - Real Word hyperlinks for emails (`mailto:`) and profiles with blue underline styling.
  - Professional summary paragraph directly below contact info.
- **Section Layout & Rule Dividers:**
  - Upper-case bold section headings (9.5pt) with single bottom border rules.
  - Automatic suppression of empty sections (e.g. empty `\section{CERTIFICATIONS}`).
- **Experience & Education Subheadings:**
  - Experience: Company / Title on left, start – end dates right-aligned via tab stops.
  - Education: Institution on line 1 with right-aligned dates, Degree on line 2 in italics.
- **Project Blocks:**
  - Bold project title, clickable project hyperlinks (`[Link]`), pipe separator (`|`), italic tech stack.
- **Bullet Lists:**
  - List Bullet style with 0.15-inch left indent, 9.5pt font, compact vertical line spacing.
- **Inline Text Formatting:**
  - Robust recursive parser for nested `\textbf{...}`, `\textit{...}`, `\emph{...}`, `\underline{...}`, `\href{url}{label}`.
  - Total elimination of LaTeX artifacts (`\hspace`, `\vspace`, `\textbullet`, `$$`, `%`, unescaped braces).

## 3. Non-Functional & Testing Requirements
- Fast (<100ms conversion), pure Python (`python-docx`).
- Comprehensive test coverage in `backend/tests/test_docx.py` verifying headers, projects, subheadings, links, formatting, and empty section omission.
