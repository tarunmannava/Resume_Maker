# -*- coding: utf-8 -*-
"""
Generate the 5 canonical base LaTeX archetype templates from the golden reference DOCX files:
1. ai.tex (TarunMannava.docx)
2. java.tex (TarunMannava_SoftwareEngineer.docx)
3. dotnet.tex (TarunMannava_DotnetDeveloper.docx)
4. node.tex (TarunMannava_SE.docx)
5. python.tex (TarunMannava_SoftwareDeveloper.docx)
"""
import os
import re
from pathlib import Path
import docx

ROOT = Path(__file__).resolve().parents[1]
ARCHETYPES_DIR = ROOT / "backend" / "app" / "templates" / "archetypes"
ARCHETYPES_DIR.mkdir(parents=True, exist_ok=True)

LATEX_PREAMBLE = r"""\documentclass[a4paper,10pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{mathptmx}
\usepackage{geometry}
\usepackage{setspace}
\usepackage{anyfontsize}

\geometry{
  a4paper,
  top=0.35in,
  bottom=0.35in,
  left=0.4in,
  right=0.4in
}

\setstretch{1.0}
\renewcommand{\normalsize}{\fontsize{10}{12}\selectfont}
\renewcommand{\small}{\fontsize{10}{12}\selectfont}
\normalsize

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-10pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-7pt}]

\newcommand{\resumeSep}{\textbullet}

\newcommand{\resumeItem}[1]{
  \item\small{#1}
}

\newcommand{\resumeSubheading}[4]{%
  \vspace{0pt}\item
  \textbf{#1} \\
  \textit{\small #2} \\
  \small #3 -- #4
  \vspace{2pt}
}

\newcommand{\resumeProject}[2]{%
  \vspace{0pt}\item[]
  \textbf{#1} \\
  \small\textit{#2}
  \vspace{2pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}

\newcommand{\resumeItemListStart}{%
  \begin{itemize}[leftmargin=0.15in, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt, label={$\bullet$}]%
}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{2pt}}

\newcommand{\resumeHeadingContact}{%
  LOCATION \hspace{0.4em}\resumeSep\hspace{0.4em}+1 (656) 203-7074 \hspace{0.4em}\resumeSep\hspace{0.4em}\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \hspace{0.4em}\resumeSep\hspace{0.4em}\href{https://github.com/tarunmannava}{GitHub}%
}

\begin{document}
"""

def escape_tex(text: str) -> str:
    # Replace unicode dashes and bullets
    text = text.replace("—", "--").replace("–", "--").replace("•", "")
    text = text.replace("%", r"\%").replace("&", r"\&").replace("#", r"\#")
    text = text.replace("$", r"\$").replace("_", r"\_")
    return text

print("Archetypes directory ready:", ARCHETYPES_DIR)
