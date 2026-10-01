# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

def add_hyperlink(paragraph: Paragraph, url: str, label: str, size: float = 9.5):
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    r_pr.append(u)
    
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    r_pr.append(color)
    
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    r_pr.append(sz)
    
    new_run.append(r_pr)
    t = OxmlElement("w:t")
    t.text = label
    t.set(qn("xml:space"), "preserve")
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

def add_section_heading(doc: Document, title: str):
    p = doc.add_paragraph()
    run = p.add_run(title.upper())
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    
    p_pr = p._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)

def add_bullet(doc: Document, text: str):
    p = doc.add_paragraph(style="List Bullet")
    p.clear()
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(9.5)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Inches(0.2)

def add_project_heading(doc: Document, title: str, tech_stack: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.keep_with_next = True
    
    r_title = p.add_run(title)
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(9.5)
    
    r_sep = p.add_run(" | ")
    r_sep.font.name = "Times New Roman"
    r_sep.font.size = Pt(9.5)
    
    r_tech = p.add_run(tech_stack)
    r_tech.italic = True
    r_tech.font.name = "Times New Roman"
    r_tech.font.size = Pt(9.5)

def add_subheading(doc: Document, org: str, role: str, dates: str):
    p = doc.add_paragraph()
    p.paragraph_format.tab_stops.add_tab_stop(Inches(7.7), WD_TAB_ALIGNMENT.RIGHT)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.keep_with_next = True
    
    r_org = p.add_run(org)
    r_org.bold = True
    r_org.font.name = "Times New Roman"
    r_org.font.size = Pt(9.5)
    
    r_div = p.add_run(" | ")
    r_div.font.name = "Times New Roman"
    r_div.font.size = Pt(9.5)
    
    r_role = p.add_run(role)
    r_role.bold = True
    r_role.italic = True
    r_role.font.name = "Times New Roman"
    r_role.font.size = Pt(9.5)
    
    p.add_run("\t")
    
    r_date = p.add_run(dates)
    r_date.bold = True
    r_date.font.name = "Times New Roman"
    r_date.font.size = Pt(9.5)

def build_resume(output_path: Path):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.4)
        section.bottom_margin = Inches(0.4)
        section.left_margin = Inches(0.4)
        section.right_margin = Inches(0.4)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(9.5)
    style.paragraph_format.line_spacing = 1.05
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.space_after = Pt(0)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    # Name
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(2)
    run_name = p_name.add_run("TARUN MANNAVA")
    run_name.bold = True
    run_name.font.name = "Times New Roman"
    run_name.font.size = Pt(17)

    # Contact line
    p_contact = doc.add_paragraph()
    p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_contact.paragraph_format.space_before = Pt(0)
    p_contact.paragraph_format.space_after = Pt(3)
    
    r = p_contact.add_run("Seattle, WA • +1 (656) 203-7074 • ")
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    
    add_hyperlink(p_contact, "mailto:mannava.tarun34@gmail.com", "mannava.tarun34@gmail.com")
    
    r = p_contact.add_run(" • ")
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    
    add_hyperlink(p_contact, "https://linkedin.com/in/tarunmannava", "LinkedIn")
    
    r = p_contact.add_run(" • ")
    r.font.name = "Times New Roman"
    r.font.size = Pt(9.5)
    
    add_hyperlink(p_contact, "https://github.com/tarunmannava", "GitHub")

    # SUMMARY
    add_section_heading(doc, "SUMMARY")
    p_sum = doc.add_paragraph()
    p_sum.paragraph_format.space_before = Pt(1)
    p_sum.paragraph_format.space_after = Pt(2)
    r_sum = p_sum.add_run(
        "AI & Software Engineer with 4+ years of experience engineering scalable backend and production LLM systems. "
        "Specializing in LangGraph multi-agent orchestration, MCP tool integration, Agentic Corrective RAG, and LangSmith evaluation pipelines. "
        "Backed by an enterprise foundation in high-throughput microservices, asynchronous execution, PostgreSQL, Redis caching, and scalable cloud infrastructure on AWS."
    )
    r_sum.font.name = "Times New Roman"
    r_sum.font.size = Pt(9.5)

    # SKILLS
    add_section_heading(doc, "SKILLS")
    skills = [
        ("GenAI & Agents:", " LangChain, LangGraph, StateGraph, Supervisor-Worker, Tool Calling, Agentic RAG, Corrective RAG, Hybrid Search, Reranking, MCP, A2A, Prompt Engineering"),
        ("LLMOps:", " LangSmith Tracing/Evals/Datasets, RAGAS, LLM-as-Judge, Golden Sets, Citation/Hallucination Evals, Cost/Latency Tracking"),
        ("Languages:", " Python, SQL, TypeScript, JavaScript, Java"),
        ("Backend:", " FastAPI, Django, Flask, AsyncIO, Java 11, Spring Boot, REST, WebSockets, Microservices, Pydantic, SQLAlchemy, Spring Data JPA/Hibernate"),
        ("Retrieval:", " PostgreSQL (pgvector) / Supabase, Qdrant, Pinecone, SQL Server, MongoDB, HNSW Indexing, Embeddings, BM25+Dense + RRF, Reranking"),
        ("Cloud & Infra:", " AWS (EC2, S3, RDS, Lambda, Cognito, CloudWatch), GCP (Vertex AI, Cloud Run, Cloud Storage), Azure (Blob Storage, App Services), Docker, Kubernetes, Linux, GitHub Actions, Redis, RabbitMQ"),
        ("Auth/Test:", " OAuth2 PKCE, JWT, AWS Cognito, Spring Security, pytest, JUnit 5, Mockito"),
    ]
    for category, items in skills:
        p_sk = doc.add_paragraph()
        p_sk.paragraph_format.space_before = Pt(0)
        p_sk.paragraph_format.space_after = Pt(1)
        r_cat = p_sk.add_run(category)
        r_cat.bold = True
        r_cat.font.name = "Times New Roman"
        r_cat.font.size = Pt(9.5)
        r_it = p_sk.add_run(items)
        r_it.font.name = "Times New Roman"
        r_it.font.size = Pt(9.5)

    # EXPERIENCE
    add_section_heading(doc, "EXPERIENCE")
    
    # 1. USF
    add_subheading(doc, "University of South Florida", "Research Assistant, Software Engineer", "Jan 2025 – May 2026")
    usf_bullets = [
        "Architected and maintained a production AI & Health Literacy web platform for the USF SHIELD Lab, building 13 interactive modules in React and TypeScript that serve 60+ biomedical students and faculty in daily coursework and research activities.",
        "Engineered a Python/FastAPI backend and a real-time dual-model sandbox integrating Groq and Hugging Face LLM APIs, with semantic grading rubrics, milestone detection, and caching that keeps interactive response latency below 2 seconds.",
        "Implemented an in-browser prompt evaluation engine using Transformers.js (WASM/ONNX) to compute cosine-similarity embedding scoring locally, providing zero-latency, privacy-preserving feedback on prompt structure and constraints.",
        "Built authentication and session management with Hugging Face OAuth2 (PKCE), engineered cloud asset and artifact storage pipelines across AWS (S3, EC2) and GCP, and designed Supabase PostgreSQL relational schemas and server-side RPCs for access code verification, quiz scoring, and deterministic chat logging.",
        "Used Python Pytest to test API endpoints, data validators, and database access paths, and wrote deployment documentation to help onboard researchers and student developers for hands-on development across semesters.",
        "Collaborated with SHIELD Lab faculty and other graduate researchers in iterative sprints, translating evolving requirements into executable tasks, code reviews, and shared runbooks for system maintenance.",
    ]
    for b in usf_bullets:
        add_bullet(doc, b)

    # 2. Cognizant
    add_subheading(doc, "Cognizant Technology Solutions", "Software Development Engineer", "Feb 2022 – Aug 2024")
    cts_bullets = [
        "Developed Java 11 and Spring Boot microservices for policy onboarding and validation with RESTful APIs, persisting client metadata in MongoDB and relational records in SQL Server, handling 20K+ peak hourly requests.",
        "Enhanced async validation workflows using CompletableFuture and ExecutorService for parallel task execution, improving request latency.",
        "Implemented multi-tier Redis caching with warm-up to reduce SQL Server load and improve p95 latency during peak onboarding traffic.",
        "Optimized audit and reporting queries using Spring Data JPA with Hibernate across PostgreSQL and SQL Server, eliminating N+1 patterns and reducing round trips.",
        "Refactored duplicate logic across 8+ microservices into reusable Spring Boot service-layer components with centralized exception handling and request validation.",
        "Implemented Spring Security OAuth2 with AWS Cognito, utilizing AWS cloud infrastructure (EC2, S3, RDS) for policy record management, and securing REST endpoints with JWT authentication and RBAC.",
        "Developed JUnit 5 and Mockito suites covering business-critical workflows, achieving 70% coverage while reducing regressions.",
    ]
    for b in cts_bullets:
        add_bullet(doc, b)

    # PROJECTS
    add_section_heading(doc, "PROJECTS")
    
    # 1. JobPilot
    add_project_heading(doc, "JobPilot: Conversational Job-Search & Ranking Agent", "Python, LangGraph, LangChain, MCP, Dice MCP, LangSmith")
    jp_bullets = [
        "Built a conversational agent that extracts a user's resume and job preferences through natural-language chat, confirming extracted criteria with the user before taking any downstream action.",
        "Integrated the Dice MCP server as a tool-use client to retrieve live job listings, consuming an MCP server end-to-end after building MCP servers in AutoDocs.",
        "Implemented a resume-to-listing ranking step that scores and orders retrieved jobs against the user's parsed resume and stated preferences.",
        "Instrumented the agent with LangSmith tracing and pass/fail scoring on tool-call correctness, giving visibility into the confirmation, retrieval, and ranking steps of each run.",
    ]
    for b in jp_bullets:
        add_bullet(doc, b)

    # 2. AutoDocs
    add_project_heading(doc, "AutoDocs: Event-Driven MCP & Multi-Agent Documentation System", "Python, FastAPI, MCP, A2A, LangGraph, LangChain, RabbitMQ, WebSockets, Supabase, GitHub Webhooks, LangSmith")
    ad_bullets = [
        "Built an event-driven documentation system receiving GitHub pull-request webhooks through FastAPI, validating HMAC-SHA256 signatures and enforcing idempotent delivery persistence in Supabase.",
        "Implemented asynchronous job processing with RabbitMQ, separating webhook ingestion from repository analysis and long-running documentation workflows with retry and failure handling.",
        "Implemented WebSocket-based real-time job updates, streaming repository-analysis status and agent progress to connected clients while supporting connection recovery and graceful handling of dropped connections.",
        "Designed Model Context Protocol (MCP) code-intelligence servers using AST analysis to extract class and function call graphs and provide structural repository context to LLMs.",
        "Architected dynamic task-routing multi-agent workflows with LangGraph to analyze code changes and generate contextual documentation with deterministic verification guardrails.",
        "Instrumented full LLM observability with LangSmith, tracing MCP tool-call sequences and LangGraph routing decisions per run and scoring each against expected tool-call patterns, achieving a 90%+ pass rate on tool-call correctness.",
    ]
    for b in ad_bullets:
        add_bullet(doc, b)

    # 3. FinScope
    add_project_heading(doc, "FinScope: Hierarchical Earnings Intelligence Graph", "Python, LangGraph, LangChain, SEC-API, Tavily, LangSmith")
    fs_bullets = [
        "Built a hierarchical multi-agent system for earnings analysis that routes filings through specialized analyst nodes, synthesizing ratio analysis and risk review into a structured investment memo.",
        "Implemented LangGraph supervisor-worker routing with shared Pydantic financial state, delegating fetch, calculation, and review steps across isolated nodes with conditional edges for low-confidence escalation.",
        "Integrated SEC-API and Tavily web search as LangChain tool nodes to retrieve live filings and market context, adding numeric validation to block incorrect margin and return calculations before synthesis.",
        "Implemented human-approval interrupt that pauses execution for analyst review when confidence scores fall below threshold, with checkpointed state for resume and audit.",
        "Architected deterministic verification guardrails requiring sourced numbers for every ratio claim, rejecting unsupported outputs and retrying failed tool calls with backoff.",
        "Instrumented full trajectory observability with LangSmith, tracing node-level decisions and tool-call sequences per run and scoring each against a 20-ticker golden dataset for numeric accuracy and faithfulness, with per-node latency and cost tracking.",
    ]
    for b in fs_bullets:
        add_bullet(doc, b)

    # 4. ProofStack
    add_project_heading(doc, "ProofStack: MCP-Backed Corrective Retrieval Graph", "Python, FastAPI, LangGraph, LangChain MCP, PostgreSQL (pgvector), Tavily, LangSmith")
    ps_bullets = [
        "Built a corrective RAG system that answers questions over internal docs by routing all retrieval through MCP tool servers, falling back to web search only when graded evidence is insufficient.",
        "Implemented LangGraph retrieve-grade-rewrite loop that rewrites ambiguous queries, retrieves via MCP tools, grades document relevance, and regenerates answers until grounding threshold is met.",
        "Designed three Model Context Protocol servers as LangChain tools — vector_search over PostgreSQL (pgvector HNSW) with dense-lexical hybrid ranking, docs_sql for structured records, and web_search via Tavily — with timeout, retry, and schema validation.",
        "Implemented WebSocket-compatible FastAPI serving layer streaming retrieval status and token output while enforcing citation-required generation with abstention on low-evidence queries.",
        "Architected verification guardrails with grounding-score gates and Pydantic-validated RAG state to prevent hallucinated citations and enforce idempotent query handling.",
        "Instrumented full LLM observability with LangSmith, tracing MCP tool-call sequences and routing decisions per run and scoring each against a 50-query golden set for faithfulness, recall@5, and citation precision, with per-route cost and p50/p95 tracking.",
    ]
    for b in ps_bullets:
        add_bullet(doc, b)

    # EDUCATION
    add_section_heading(doc, "EDUCATION")
    p_edu = doc.add_paragraph()
    p_edu.paragraph_format.tab_stops.add_tab_stop(Inches(7.7), WD_TAB_ALIGNMENT.RIGHT)
    p_edu.paragraph_format.space_before = Pt(2)
    p_edu.paragraph_format.space_after = Pt(0)
    p_edu.paragraph_format.keep_with_next = True
    r_inst = p_edu.add_run("University of South Florida, Tampa")
    r_inst.bold = True
    r_inst.font.name = "Times New Roman"
    r_inst.font.size = Pt(9.5)
    p_edu.add_run("\t")
    r_edate = p_edu.add_run("Aug 2024 – May 2026")
    r_edate.bold = True
    r_edate.font.name = "Times New Roman"
    r_edate.font.size = Pt(9.5)

    p_deg = doc.add_paragraph()
    p_deg.paragraph_format.space_before = Pt(0)
    p_deg.paragraph_format.space_after = Pt(2)
    r_deg = p_deg.add_run("Master of Science, Computer Science")
    r_deg.italic = True
    r_deg.font.name = "Times New Roman"
    r_deg.font.size = Pt(9.5)

    # CERTIFICATIONS
    add_section_heading(doc, "CERTIFICATIONS")
    certs = [
        ("AWS Certified AI Practitioner (AIF-C01)", "Amazon Web Services (AWS)"),
        ("Claude Certified Prompt Engineer", "Anthropic"),
        ("AWS Certified Cloud Practitioner", "Amazon Web Services (AWS)"),
    ]
    for cert_name, issuer in certs:
        p_c = doc.add_paragraph(style="List Bullet")
        p_c.clear()
        p_c.paragraph_format.space_before = Pt(0)
        p_c.paragraph_format.space_after = Pt(1)
        p_c.paragraph_format.left_indent = Inches(0.2)
        
        r_cname = p_c.add_run(cert_name)
        r_cname.bold = True
        r_cname.font.name = "Times New Roman"
        r_cname.font.size = Pt(9.5)
        
        r_ciss = p_c.add_run(f" – {issuer}")
        r_ciss.font.name = "Times New Roman"
        r_ciss.font.size = Pt(9.5)

    # Save to path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    target = Path(r"D:\Projects\Resume Maker\generated_resumes\TarunMannava.docx")
    build_resume(target)
