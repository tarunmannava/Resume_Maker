import pytest
from backend.app.services.latex_skills import reorder_experience_for_java


def test_reorder_experience_for_java():
    doc = """
\\section{EXPERIENCE}
\\begin{itemize}
  \\resumeSubheading
    {University of South Florida}{Jan 2025 -- May 2026}
    {Graduate Researcher}{Tampa, FL}
    \\resumeItemListStart
      \\resumeItem{Built RAG pipelines.}
    \\resumeItemListEnd

  \\resumeSubheading
    {Cognizant Technology Solutions}{Feb 2022 -- Aug 2024}
    {Software Engineer}{Hyderabad, India}
    \\resumeItemListStart
      \\resumeItem{Developed Java Spring Boot microservices.}
    \\resumeItemListEnd
\\end{itemize}
"""
    reordered = reorder_experience_for_java(doc)
    cog_pos = reordered.find("Cognizant Technology Solutions")
    usf_pos = reordered.find("University of South Florida")
    assert cog_pos != -1
    assert usf_pos != -1
    assert cog_pos < usf_pos
