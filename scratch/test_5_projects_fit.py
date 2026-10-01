# -*- coding: utf-8 -*-
import os
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
import win32com.client

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
    
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    r_pr.append(rFonts)
    
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

def add_project_heading(doc: Document, title: str, tech_stack: str, link_url: str = None, link_label: str = "Link"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.keep_with_next = True
    
    r_title = p.add_run(title)
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(9.5)
    
    if link_url:
        r_sep1 = p.add_run(" | ")
        r_sep1.font.name = "Times New Roman"
        r_sep1.font.size = Pt(9.5)
        add_hyperlink(p, link_url, link_label, size=9.5)
    
    r_sep2 = p.add_run(" | ")
    r_sep2.font.name = "Times New Roman"
    r_sep2.font.size = Pt(9.5)
    
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

def build_test(output_path: Path):
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
        "AI & Software Engineer with 4+ years of experience engineering scalable backend services and production agentic AI systems across Node.js, Python, and AWS. "
        "Specializing in multi-agent orchestration (Claude Code, LangGraph, CrewAI, AWS Bedrock), Model Context Protocol (MCP) server development, and SDLC developer productivity tooling. "
        "Proven expertise in building custom agent harnesses, enterprise API integrations, human-in-the-loop workflows, LLM observability (LangSmith, CloudWatch), and cost and telemetry controls."
    )
    r_sum.font.name = "Times New Roman"
    r_sum.font.size = Pt(9.5)

    # SKILLS
    add_section_heading(doc, "SKILLS")
    skills = [
        ("GenAI & Agents:", " Multi-Agent Workflows, Claude Code, AWS Bedrock, AgentCore, CrewAI, LangGraph, Model Context Protocol (MCP), Tool Calling, Agentic RAG, Corrective RAG, Human-in-the-Loop, Prompt Engineering"),
        ("LLMOps & Governance:", " LangSmith (Tracing, Evals, Datasets), RAGAS, LLM-as-Judge, AI Security & Governance, Telemetry & Cost Controls, Grounding Gates, Latency Tracking"),
        ("Languages:", " TypeScript, JavaScript (Node.js), Python, SQL, Java"),
        ("Backend & Tooling:", " Node.js, Express.js, NestJS, FastAPI, REST APIs, WebSockets, CLI Tooling, Custom Developer Harnesses, Microservices, Asynchronous Event Loops, Pydantic, Prisma ORM"),
        ("Cloud & AWS:", " AWS Bedrock, Lambda, EC2, S3, RDS, Cognito, CloudWatch, API Gateway, Docker, Kubernetes, Linux, GitHub Actions, Redis, RabbitMQ"),
        ("Retrieval & Data:", " PostgreSQL (pgvector) / Supabase, Qdrant, Pinecone, SQL Server, MongoDB, HNSW Indexing, Dense & Lexical Search, Reranking"),
        ("Testing & Security:", " OAuth2 PKCE, JWT, RBAC, Jest, Supertest, Pytest, JUnit 5, Mockito, SDLC Automation"),
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

    # PROJECTS (All 5 Projects: SkillBeacon, AutoDocs, JobPilot, FinScope, ProofStack)
    add_section_heading(doc, "PROJECTS")
    
    # 1. SkillBeacon (Node.js / React Career Platform)
    add_project_heading(doc, "SkillBeacon: Skills & Career Intelligence Platform", "Node.js, TypeScript, Next.js, React, Python, FastAPI, PostgreSQL, Cloudflare R2, Google OAuth2", "https://skillbeacon-six.vercel.app/", "Link")
    sb_bullets = [
        "Built a full-stack career platform with Node.js/TypeScript and Python/FastAPI backend microservices and React/Next.js frontend, supporting multi-role student, mentor, and employer workflows with PostgreSQL and Prisma ORM persistence.",
        "Implemented Skill Passport with skill proficiency tiers, evidence submissions, and multi-party confidence scoring algorithms based on mentor and employer verification signals.",
        "Architected an automated job intelligence engine with Next.js SSR data scraping, persistent CSV/JSON deduplication, and an intelligent soft-flagging system for qualification filtering.",
        "Engineered an asynchronous document generation microservice in FastAPI to dynamically tailor LaTeX templates and compile clean, ATS-compliant DOCX resumes under 2s latency.",
    ]
    for b in sb_bullets:
        add_bullet(doc, b)

    # 2. AutoDocs
    add_project_heading(doc, "AutoDocs: Event-Driven MCP & Multi-Agent Documentation System", "Node.js, TypeScript, Python, FastAPI, MCP, LangGraph, RabbitMQ, WebSockets, Supabase, GitHub Webhooks, LangSmith")
    ad_bullets = [
        "Built an event-driven developer productivity and SDLC documentation platform receiving GitHub PR webhooks, validating HMAC-SHA256 signatures and enforcing idempotent delivery persistence in Supabase.",
        "Implemented asynchronous job processing with RabbitMQ, decoupling webhook ingestion from repository AST analysis and long-running documentation workflows with retry and failure handling.",
        "Designed custom Model Context Protocol (MCP) code-intelligence servers using AST analysis to extract class and function call graphs, providing structural codebase context to LLMs.",
        "Architected dynamic task-routing multi-agent workflows with LangGraph and Claude Code developer harnesses to analyze code diffs and generate contextual documentation with deterministic verification guardrails.",
    ]
    for b in ad_bullets:
        add_bullet(doc, b)

    # 3. JobPilot
    add_project_heading(doc, "JobPilot: Conversational Job-Search & Ranking Agent", "Python, LangGraph, LangChain, MCP, Dice MCP, LangSmith, Human-in-the-Loop")
    jp_bullets = [
        "Built a conversational agent that extracts user resume criteria and job preferences through natural-language dialogue, enforcing human-in-the-loop confirmation before executing downstream searches.",
        "Integrated the Dice Model Context Protocol (MCP) server as a tool-use client to retrieve live job listings, validating tool schemas and handling graceful fallbacks.",
        "Implemented an agentic resume-to-listing ranking step scoring and prioritizing retrieved opportunities against parsed resumes and candidate constraints.",
        "Instrumented end-to-end LLM observability with LangSmith tracing and pass/fail evaluation on tool-call correctness, tracking latency, token cost, and routing fidelity per run.",
    ]
    for b in jp_bullets:
        add_bullet(doc, b)

    # 4. FinScope
    add_project_heading(doc, "FinScope: Hierarchical Earnings Intelligence Graph", "Python, LangGraph, LangChain, SEC-API, Tavily, LangSmith, Human-in-the-Loop")
    fs_bullets = [
        "Built a hierarchical multi-agent system for earnings analysis that routes filings through specialized analyst nodes, synthesizing ratio analysis and risk review into a structured investment memo.",
        "Implemented LangGraph supervisor-worker routing with shared Pydantic financial state, delegating fetch, calculation, and review steps across isolated nodes with conditional edges for low-confidence escalation.",
        "Integrated SEC-API and Tavily web search as LangChain tool nodes to retrieve live filings and market context, adding numeric validation to block incorrect calculations before synthesis.",
        "Implemented human-approval interrupt that pauses execution for analyst review when confidence scores fall below threshold, with checkpointed state for resume and audit.",
    ]
    for b in fs_bullets:
        add_bullet(doc, b)

    # 5. ProofStack
    add_project_heading(doc, "ProofStack: MCP-Backed Corrective Retrieval Graph", "Python, Node.js, FastAPI, LangGraph, MCP Protocol, PostgreSQL (pgvector), Tavily, LangSmith")
    ps_bullets = [
        "Built a corrective RAG system that answers questions over internal docs by routing all retrieval through MCP tool servers, falling back to web search only when graded evidence is insufficient.",
        "Implemented LangGraph retrieve-grade-rewrite loop that rewrites ambiguous queries, retrieves via MCP tools, grades document relevance, and regenerates answers until grounding threshold is met.",
        "Designed three Model Context Protocol servers as LangChain tools: vector_search over PostgreSQL (pgvector HNSW) with dense-lexical hybrid ranking, docs_sql for structured records, and web_search via Tavily.",
        "Architected verification guardrails with grounding-score gates and Pydantic-validated RAG state, instrumenting full LLM observability with LangSmith tracing per-route cost and latency.",
    ]
    for b in ps_bullets:
        add_bullet(doc, b)

    # EXPERIENCE (USF with Node.js backend, Cognizant)
    add_section_heading(doc, "EXPERIENCE")
    
    # 1. USF
    add_subheading(doc, "University of South Florida", "Research Assistant, Software Engineer", "Jan 2025 - May 2026")
    usf_bullets = [
        "Architected and maintained a production AI & Health Literacy web platform for the USF SHIELD Lab across 13 interactive modules (serving 60+ biomedical students and faculty), engineering Node.js and TypeScript backend microservices with Express and Prisma ORM.",
        "Engineered a real-time dual-model LLM sandbox backend in Node.js integrating AWS Bedrock and Hugging Face APIs with WebSocket/Socket.io streaming, semantic evaluation rubrics, and Redis caching that keeps response latency below 2 seconds.",
        "Implemented an in-browser prompt evaluation engine using Transformers.js (WASM/ONNX) to compute cosine-similarity embedding scoring locally, delivering zero-latency, privacy-preserving feedback on prompt constraints and structure.",
        "Built authentication and session management with OAuth2 (PKCE), engineered cloud-native asset storage and telemetry pipelines on AWS (S3, EC2, CloudWatch), and designed Supabase PostgreSQL relational schemas and server-side RPCs for deterministic chat logging and quiz scoring.",
        "Developed automated test suites using Jest and Supertest for Node.js API endpoints and database access paths, creating custom CLI developer harnesses and CI/CD workflows to accelerate module testing and deployment.",
        "Collaborated with SHIELD Lab faculty and researchers in iterative agile sprints, establishing AI security guardrails, prompt evaluation rubrics, code reviews, and shared operational runbooks for system maintenance.",
    ]
    for b in usf_bullets:
        add_bullet(doc, b)

    # 2. Cognizant
    add_subheading(doc, "Cognizant Technology Solutions", "Software Development Engineer", "Feb 2022 - Aug 2024")
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
    r_edate = p_edu.add_run("Aug 2024 - May 2026")
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
        
        r_cname = p_c.add_run(f"{cert_name} - {issuer}")
        r_cname.bold = True
        r_cname.font.name = "Times New Roman"
        r_cname.font.size = Pt(9.5)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"Saved test to {output_path}")

if __name__ == "__main__":
    t = Path("scratch/test_5_projects.docx")
    build_test(t)
