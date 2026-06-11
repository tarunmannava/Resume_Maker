import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import {
  healthCheck,
  rewriteResume,
  analyzeJob,
  compileLatex,
  toAbsoluteApiUrl,
  answerScreeningQuestion,
} from "./lib/api";
import type {
  KeywordMatch,
  RewriteMode,
  RewriteResponse,
  CompileResponse,
} from "./lib/api";
import "./styles.css";

const sampleResume = `%-------------------------
% Tarun Mannava - Resume in LaTeX
%-------------------------

\\documentclass[a4paper,11pt]{article}

\\usepackage{latexsym}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{marvosym}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{verbatim}
\\usepackage{enumitem}
\\usepackage[hidelinks]{hyperref}
\\usepackage{fancyhdr}
\\usepackage[english]{babel}
\\usepackage{tabularx}
\\usepackage{mathptmx}
\\usepackage{geometry}
\\usepackage{setspace}

% Standardized thin margins to maximize space safely
\\geometry{
  a4paper,
  top=0.35in,
  bottom=0.35in,
  left=0.4in,
  right=0.4in
}

\\setstretch{1.0}

\\pagestyle{fancy}
\\fancyhf{}
\\fancyfoot{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

\\urlstyle{same}
\\raggedbottom
\\raggedright
\\setlength{\\tabcolsep}{0in}

% Further reduced section gap (pulled up higher, tighter below the rule)
\\titleformat{\\section}{
  \\vspace{-10pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-7pt}]

\\newcommand{\\resumeItem}[1]{
  \\item\\small{#1}
}

\\newcommand{\\resumeSubheading}[4]{
  \\vspace{0pt}\\item
    \\begin{tabular*}{1.0\\textwidth}[t]{l@{\\extracolsep{\\fill}}r}
      \\textbf{#1} $|$ \\textit{\\small#2} & \\small #3 - #4 \\\\
    \\end{tabular*}\\vspace{1pt}
}

\\newcommand{\\resumeProjectHeading}[1]{
  \\vspace{0pt}\\item
    \\begin{tabular*}{1.0\\textwidth}{l@{\\extracolsep{\\fill}}r}
      \\textbf{#1} \\\\
    \\end{tabular*}\\vspace{1pt}
}

% Alias for rewriter compatibility (optional second arg = tech stack, ignored in PDF layout)
\\newcommand{\\resumeProject}[2]{\\resumeProjectHeading{#1}}

% Set all list spacing to strictly 0pt
\\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]}
\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}

\\newcommand{\\resumeItemListStart}{\\begin{itemize}[leftmargin=0.15in, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt, label=$\\bullet$]}
\\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{2pt}}

%-------------------------------------------
\\begin{document}

%---------- HEADING ----------
\\begin{center}
  {\\Huge \\textbf{Tarun Mannava}} \\\\[4pt]
  \\small
  Tampa, FL \\quad $|$ \\quad
  +1 (656) 203-7074 \\quad $|$ \\quad
  \\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \\quad $|$ \\quad
  \\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \\quad $|$ \\quad
  \\href{https://github.com/tarunmannava}{GitHub}
\\end{center}

\\vspace{-10pt}

%---------- EDUCATION ----------
\\section{EDUCATION}
\\resumeSubHeadingListStart
  \\resumeSubheading
    {University of South Florida, Tampa, United States}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\\resumeSubHeadingListEnd

%---------- EXPERIENCE ----------
\\section{EXPERIENCE}
\\resumeSubHeadingListStart

  \\resumeSubheading
    {University of South Florida}{Graduate Researcher - Full-Stack AI Platform}{Jan 2025}{Present}
  \\resumeItemListStart
    \\resumeItem{Architected and shipped an AI-powered biomedical learning platform end-to-end, designing product architecture, building all 13 interactive modules, and enabling active use by USF SHIELD Lab students and instructors.}
    \\resumeItem{Built the production frontend in \\textbf{React} and \\textbf{TypeScript}, delivering adaptive student exercises and instructor curriculum tools used across multiple course workflows.}
    \\resumeItem{Developed \\textbf{Node.js} backend services and integrated a 20B-parameter LLM via the \\textbf{Groq API}, supporting 60+ concurrent users with sub-2s response latency for model-comparison and AI-assisted learning flows.}
    \\resumeItem{Designed \\textbf{PostgreSQL} schemas for authentication, progress tracking, and role-based learning analytics, supporting multi-role access patterns across student, instructor, and researcher personas.}
    \\resumeItem{Implemented shared TypeScript contracts and validation across frontend and backend services, reducing integration defects by 30\\% and accelerating feature delivery across sprint cycles.}
    \\resumeItem{Translated researcher and student feedback into production releases on 2-week iteration cycles, shipping 8+ major module updates without disrupting live classroom usage.}
  \\resumeItemListEnd

  \\resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \\resumeItemListStart
    \\resumeItem{Developed customer-facing \\textbf{Java/Spring Boot} REST APIs for registration, validation, and authentication workflows supporting \\textbf{20K+ hourly peak transactions} across customer onboarding and account management.}
    \\resumeItem{Implemented business rules and input-validation services in \\textbf{Java} and \\textbf{SQL}, reducing downstream processing errors by 18\\% across high-volume registration flows.}
    \\resumeItem{Leveraged \\textbf{Redis} for session and token caching on authentication endpoints, improving p95 response times by 30\\% and lowering database load on hot read paths.}
    \\resumeItem{Designed integrations with \\textbf{MongoDB} and \\textbf{SQL Server} for customer profile and transactional data, supporting reliable reads/writes under peak onboarding traffic.}
    \\resumeItem{Standardized REST request/response contracts across microservices, cutting frontend-backend integration defects by 25\\% and improving release stability for consuming teams.}
    \\resumeItem{Built automated test coverage with \\textbf{JUnit} and \\textbf{Cucumber}, reaching 70\\% backend coverage and reducing production regressions on critical auth paths.}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- PROJECTS ----------
\\section{PROJECTS}
\\resumeSubHeadingListStart

  \\resumeProjectHeading{Centralized Prompt Registry for Clinical AI Experimentation}
  \\resumeItemListStart
    \\resumeItem{Developed a centralized prompt registry microservice for clinical LLM applications, supporting versioning, rollback, and dynamic rendering across 40+ production AI workflows.}
    \\resumeItem{Implemented real-time A/B experimentation infrastructure for OpenAI and Gemini models on treatment-recommendation tasks, improving winning-variant selection speed by 3x.}
    \\resumeItem{Built observability dashboards tracking latency, token throughput, cost, and generation quality, reducing mean time to detect anomalies by 40\\%.}
    \\resumeItem{Designed canary traffic routing for production prompt rollouts, enabling zero-downtime updates across 12 prompt families in a healthcare environment.}
  \\resumeItemListEnd

  \\resumeProjectHeading{Scalable LLM Infrastructure for Clinical Note Summarization}
  \\resumeItemListStart
    \\resumeItem{Containerized and orchestrated open-source LLM inference services on \\textbf{AWS} with GPU autoscaling, supporting 10x traffic spikes without manual intervention for clinical note summarization.}
    \\resumeItem{Implemented Infrastructure-as-Code with \\textbf{Terraform} and \\textbf{GitHub Actions} CI/CD, reducing environment provisioning time from 4 hours to 25 minutes.}
    \\resumeItem{Integrated \\textbf{Prometheus} and \\textbf{Grafana} monitoring, achieving 99.9\\% uptime across production AI inference workloads.}
    \\resumeItem{Optimized inference via quantization and distributed serving, increasing throughput by 2.4x while holding p95 latency under 800ms.}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- SKILLS ----------
\\section{SKILLS}
\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \\small{\\item{
    \\textbf{Languages:} TypeScript $|$ Python $|$ Java $|$ SQL \\\\[1pt]
    \\textbf{Frontend \\& Backend:} React $|$ Next.js $|$ HTML/CSS $|$ Node.js $|$ Express.js $|$ Spring Boot $|$ FastAPI $|$ REST APIs $|$ Microservices \\\\[1pt]
    \\textbf{Data \\& Cloud:} PostgreSQL $|$ MongoDB $|$ Redis $|$ SQL Server $|$ AWS $|$ Docker $|$ Jenkins $|$ GitHub Actions $|$ Linux \\\\[1pt]
    \\textbf{AI \\& Observability:} LangChain $|$ LLM Integration $|$ Prompt Engineering $|$ Prometheus $|$ Grafana \\\\[1pt]
    \\textbf{Testing:} Jest $|$ Cypress $|$ JUnit \\\\[1pt]
    \\textbf{Programming Concepts:} APIs $|$ OOP
  }}
\\end{itemize}

%---------- CERTIFICATIONS ----------
\\section{CERTIFICATIONS}
\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \\small{\\item{
    \\textbf{AWS Certified Cloud Practitioner} - Amazon, Nov 2023
  }}
\\end{itemize}

%-------------------------------------------
\\end{document}`;

const sampleJob = `Required: Python, Django, PostgreSQL, REST APIs, AWS.
Preferred: React or Angular, Docker, CI/CD.
We value backend engineers who can build scalable services and collaborate across teams.`;

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function KeywordTable({
  title,
  items,
  onToggle,
  selectedItems = [],
}: {
  title: string;
  items: KeywordMatch[];
  onToggle?: (term: string) => void;
  selectedItems?: string[];
}) {
  if (!items.length) {
    return (
      <section className="card small-card">
        <h3>{title}</h3>
        <p className="muted">None</p>
      </section>
    );
  }

  return (
    <section className="card small-card">
      <h3>{title}</h3>
      <div className="keyword-list">
        {items.slice(0, 20).map((item) => (
          <div
            className={`keyword ${item.risk} ${onToggle ? "interactive" : ""}`}
            key={`${item.term}-${item.status}`}
            onClick={() => onToggle?.(item.term)}
          >
            <div className="keyword-core">
              {onToggle && (
                <input
                  type="checkbox"
                  checked={selectedItems.includes(item.term)}
                  readOnly
                />
              )}
              <div>
                <strong>{item.term}</strong>
                <span>
                  {item.category} · {item.status}
                </span>
              </div>
            </div>
            <em>{item.risk}</em>
          </div>
        ))}
      </div>
    </section>
  );
}

type ScreeningExchange = {
  question: string;
  answer: string;
};

function ScreeningPanel({
  jobDescription,
  resumeLatex,
  companyContext,
  roleName,
  companyName,
}: {
  jobDescription: string;
  resumeLatex: string;
  companyContext: string;
  roleName: string;
  companyName: string;
}) {
  const [customQuestion, setCustomQuestion] = useState("");
  const [activeQuestion, setActiveQuestion] = useState("");
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [history, setHistory] = useState<ScreeningExchange[]>([]);
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [screeningError, setScreeningError] = useState<string | null>(null);
  const [answerWarning, setAnswerWarning] = useState<string | null>(null);

  const canUseScreening =
    jobDescription.trim().length >= 20 && resumeLatex.trim().length >= 20;

  async function handleAskQuestion(question: string) {
    const trimmed = question.trim();
    if (!canUseScreening || loadingAnswer || trimmed.length < 3) return;

    setLoadingAnswer(true);
    setScreeningError(null);
    setAnswerWarning(null);
    setActiveQuestion(trimmed);
    setCurrentAnswer("");
    setCustomQuestion(trimmed);

    try {
      const response = await answerScreeningQuestion({
        job_description: jobDescription,
        resume_latex: resumeLatex,
        question: trimmed,
        company_context: companyContext || null,
        role_name: roleName || null,
        company_name: companyName || null,
      });
      setCurrentAnswer(response.answer);
      setHistory((prev) => [
        { question: response.question, answer: response.answer },
        ...prev.filter((item) => item.question !== response.question),
      ]);
      setAnswerWarning(response.warning ?? null);
    } catch (err) {
      setScreeningError(
        err instanceof Error ? err.message : "Failed to generate answer",
      );
    } finally {
      setLoadingAnswer(false);
    }
  }

  async function copyAnswer() {
    if (!currentAnswer) return;
    await navigator.clipboard.writeText(currentAnswer);
  }

  return (
    <section className="card screening-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Application Prep</p>
          <h2>Screening Question Assistant</h2>
        </div>
      </div>

      <p className="muted screening-intro">
        Paste a screening question from the application form and get an answer grounded in your resume and this job description.
      </p>

      {!canUseScreening && (
        <p className="warning">Add a job description and resume (20+ chars each) to use screening Q&amp;A.</p>
      )}

      {answerWarning && <p className="warning">{answerWarning}</p>}
      {screeningError && <p className="error">{screeningError}</p>}

      <div className="screening-ask">
        <label>
          Screening question
          <textarea
            className="short"
            value={customQuestion}
            onChange={(event) => setCustomQuestion(event.target.value)}
            placeholder="Paste a screening question from the application form, or write your own..."
            rows={3}
          />
        </label>
        <button
          type="button"
          onClick={() => handleAskQuestion(customQuestion)}
          disabled={!canUseScreening || loadingAnswer || customQuestion.trim().length < 3}
        >
          {loadingAnswer ? "Generating answer..." : "Get Answer"}
        </button>
      </div>

      {(activeQuestion || currentAnswer) && (
        <div className="screening-answer">
          <h3>Answer</h3>
          {activeQuestion && (
            <p className="screening-question">
              <strong>Q:</strong> {activeQuestion}
            </p>
          )}
          {loadingAnswer ? (
            <p className="muted">Drafting an answer from your resume and the job description...</p>
          ) : (
            <>
              <div className="answer-box">{currentAnswer}</div>
              <button type="button" className="secondary" onClick={copyAnswer} disabled={!currentAnswer}>
                Copy answer
              </button>
            </>
          )}
        </div>
      )}

      {history.length > 1 && (
        <div className="screening-history">
          <h3>Previous answers</h3>
          {history.slice(1, 4).map((item) => (
            <button
              key={item.question}
              type="button"
              className="history-item"
              onClick={() => {
                setActiveQuestion(item.question);
                setCurrentAnswer(item.answer);
                setCustomQuestion(item.question);
              }}
            >
              <strong>{item.question}</strong>
              <span>{item.answer.slice(0, 120)}{item.answer.length > 120 ? "…" : ""}</span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

export default function App() {
  const [jobDescription, setJobDescription] = useState(sampleJob);
  const [resumeLatex, setResumeLatex] = useState(sampleResume);
  const [candidateName, setCandidateName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [roleName, setRoleName] = useState("");
  const [companyContext, setCompanyContext] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState("Don't know");
  const [customIndustry, setCustomIndustry] = useState("");
  const [selectedRoleCategory, setSelectedRoleCategory] = useState("Software Engineer");
  const [detectedIndustry, setDetectedIndustry] = useState<string | null>(null);
  const [detectedRoleCategory, setDetectedRoleCategory] = useState<string | null>(null);
  const [showIndustryWarning, setShowIndustryWarning] = useState(false);
  const [analyzingJob, setAnalyzingJob] = useState(false);
  const [compiling, setCompiling] = useState(false);
  const [compileResult, setCompileResult] = useState<CompileResponse | null>(null);
  const [compileError, setCompileError] = useState<string | null>(null);
  const [extraNotes, setExtraNotes] = useState(
    "Keep it ATS friendly and preserve LaTeX structure.",
  );
  const [confirmedSkills, setConfirmedSkills] = useState("");
  const [bannedSkills, setBannedSkills] = useState("");
  const [rewriteMode, setRewriteMode] = useState<RewriteMode>("transferable");
  const [targetThreshold, setTargetThreshold] = useState(75);
  const [alignTitles, setAlignTitles] = useState(false);
  const [result, setResult] = useState<RewriteResponse | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [selectedMissingSkills, setSelectedMissingSkills] = useState<string[]>(
    [],
  );

  async function handleAnalyzeJob() {
    if (jobDescription.trim().length < 20 || analyzingJob) return;
    setAnalyzingJob(true);
    try {
      const response = await analyzeJob({
        job_description: jobDescription,
        company_context: companyContext || null,
      });
      setDetectedIndustry(response.detected_industry);
      setDetectedRoleCategory(response.detected_role_category);
      
      if (response.detected_role_category) {
        setSelectedRoleCategory(response.detected_role_category);
      }
      
      if (response.detected_industry) {
        setSelectedIndustry(response.detected_industry);
        setShowIndustryWarning(false);
      } else {
        setSelectedIndustry("Don't know");
        setShowIndustryWarning(true);
      }
    } catch (err) {
      console.error("Failed to analyze job details", err);
    } finally {
      setAnalyzingJob(false);
    }
  }

  async function handleCompile() {
    if (!result?.rewritten_latex) return;
    setCompiling(true);
    setCompileError(null);
    setCompileResult(null);
    try {
      const res = await compileLatex({
        latex_code: result.rewritten_latex,
        candidate_name: candidateName || "Resume",
        company_name: companyName || "General",
        role_name: roleName || "Position",
      });
      setCompileResult(res);
      if (res.success && res.pdf_download_url) {
        window.open(toAbsoluteApiUrl(res.pdf_download_url), "_blank");
      } else if (!res.success) {
        setCompileError(res.errors.join("\n"));
      }
    } catch (caught) {
      setCompileError(caught instanceof Error ? caught.message : "Unknown compilation error");
    } finally {
      setCompiling(false);
    }
  }

  function downloadTex() {
    if (!result?.rewritten_latex) return;
    const blob = new Blob([result.rewritten_latex], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const safeName = candidateName ? candidateName.replace(/\s+/g, "_") : "Resume";
    link.download = `${safeName}.tex`;
    link.click();
    URL.revokeObjectURL(url);
  }

  useEffect(() => {
    healthCheck().then(setBackendOnline);
  }, []);

  const canSubmit = useMemo(() => {
    return (
      jobDescription.trim().length >= 20 &&
      resumeLatex.trim().length >= 20 &&
      !loading
    );
  }, [jobDescription, resumeLatex, loading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setCopied(false);
    setResult(null);

    try {
      const response = await rewriteResume({
        job_description: jobDescription,
        resume_latex: resumeLatex,
        candidate_name: candidateName,
        company_name: companyName,
        role_name: roleName,
        company_context: companyContext || null,
        rewrite_mode: rewriteMode,
        target_match_threshold: targetThreshold,
        confirmed_skills: [
          ...splitCsv(confirmedSkills),
          ...selectedMissingSkills,
        ],
        banned_skills: splitCsv(bannedSkills),
        extra_user_notes: extraNotes || null,
        align_titles: alignTitles,
        selected_industry: selectedIndustry === "Other" ? customIndustry : selectedIndustry,
        selected_role_category: selectedRoleCategory,
      });
      setResult(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function copyLatex() {
    if (!result?.rewritten_latex) return;
    await navigator.clipboard.writeText(result.rewritten_latex);
    setCopied(true);
  }
  
  function toggleMissingSkill(term: string) {
    setSelectedMissingSkills((prev) =>
      prev.includes(term) ? prev.filter((t) => t !== term) : [...prev, term],
    );
  }

  const screeningResumeLatex = result?.rewritten_latex ?? resumeLatex;

  // Removed handleCompileOnly as requested.

  return (
    <main className="page-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">ATS LaTeX Resume Rewriter</p>
          <h1>Paste a job description and your current resume.</h1>
          <p>
            The frontend sends both to your FastAPI backend, which uses Gemini
            to rewrite the resume and return LaTeX plus a keyword report.
          </p>
        </div>
        <div
          className={`status ${backendOnline ? "online" : backendOnline === false ? "offline" : ""}`}
        >
          Backend:{" "}
          {backendOnline === null
            ? "checking..."
            : backendOnline
              ? "online"
              : "offline"}
        </div>
      </header>

      <form className="grid" onSubmit={handleSubmit}>
        <section className="card editor-card">
          <div className="section-heading">
            <h2>Job Description</h2>
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <button
                type="button"
                className="secondary"
                style={{ padding: "6px 12px", borderRadius: "8px", fontSize: "12px" }}
                onClick={handleAnalyzeJob}
                disabled={jobDescription.length < 20 || analyzingJob}
              >
                {analyzingJob ? "Analyzing..." : "Detect Role & Industry"}
              </button>
              <span>{jobDescription.length} chars</span>
            </div>
          </div>
          <textarea
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            onBlur={handleAnalyzeJob}
            placeholder="Paste the job description here..."
          />
        </section>

        <section className="card editor-card">
          <div className="section-heading">
            <h2>Current LaTeX Resume</h2>
            <span>{resumeLatex.length} chars</span>
          </div>
          <textarea
            value={resumeLatex}
            onChange={(event) => setResumeLatex(event.target.value)}
          />
        </section>

        <section className="card settings-card">
          <h2>Rewrite Settings</h2>

          {showIndustryWarning && (
            <div className="warning" style={{ margin: "0 0 14px 0", fontSize: "14px" }}>
              ⚠️ We couldn't auto-detect the industry from the job description. Please select a specific industry below to customize projects and experience, or select "Don't know" to match by keywords.
            </div>
          )}

          {detectedRoleCategory && (
            <div className="status online" style={{ margin: "0 0 14px 0", fontSize: "14px", display: "inline-block", alignSelf: "flex-start" }}>
              ✨ Auto-detected Role Category: <strong>{detectedRoleCategory}</strong>
              {detectedIndustry ? ` · Industry: ${detectedIndustry}` : ""}
            </div>
          )}

          <div className="settings-grid">
            <label>
              Candidate name
              <input
                value={candidateName}
                onChange={(event) => setCandidateName(event.target.value)}
                placeholder="Tarun Kumar"
              />
            </label>
            <label>
              Company name
              <input
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                placeholder="Google"
              />
            </label>
            <label>
              Role name
              <input
                value={roleName}
                onChange={(event) => setRoleName(event.target.value)}
                placeholder="Java Developer"
              />
            </label>
            <label>
              Rewrite mode
              <select
                value={rewriteMode}
                onChange={(event) =>
                  setRewriteMode(event.target.value as RewriteMode)
                }
              >
                <option value="strict">Strict</option>
                <option value="transferable">Transferable</option>
                <option value="user_verified">User verified</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </label>
            <label>
              Role Category
              <select
                value={selectedRoleCategory}
                onChange={(event) => setSelectedRoleCategory(event.target.value)}
              >
                <option value="Software Engineer">Software Engineer</option>
                <option value="AI Engineer">AI Engineer</option>
                <option value="AI Support">AI Support / Infra</option>
                <option value="ML Engineer">ML Engineer</option>
              </select>
            </label>
            <label>
              Company Industry
              <select
                value={selectedIndustry}
                onChange={(event) => {
                  setSelectedIndustry(event.target.value);
                  if (event.target.value !== "Other") {
                    setShowIndustryWarning(false);
                  }
                }}
              >
                <option value="Don't know">Don't know (auto-match)</option>
                <option value="Fintech">Fintech / Finance</option>
                <option value="Healthcare">Healthcare / Biotech</option>
                <option value="E-commerce">E-commerce / Retail</option>
                <option value="Cybersecurity">Cybersecurity</option>
                <option value="SaaS">SaaS / Cloud</option>
                <option value="Edtech">Edtech / Education</option>
                <option value="Media">Media / Entertainment</option>
                <option value="Other">Other (specify...)</option>
              </select>
            </label>
            {selectedIndustry === "Other" && (
              <label>
                Specify Industry
                <input
                  value={customIndustry}
                  onChange={(event) => setCustomIndustry(event.target.value)}
                  placeholder="e.g. Logistics, Aerospace"
                />
              </label>
            )}
            <label>
              Target match %
              <input
                type="number"
                min="1"
                max="100"
                value={targetThreshold}
                onChange={(event) =>
                  setTargetThreshold(Number(event.target.value))
                }
              />
            </label>
            <label>
              Confirmed skills, comma-separated
              <input
                value={confirmedSkills}
                onChange={(event) => setConfirmedSkills(event.target.value)}
                placeholder="Angular, Django, C++"
              />
            </label>
            <label>
              Banned skills, comma-separated
              <input
                value={bannedSkills}
                onChange={(event) => setBannedSkills(event.target.value)}
                placeholder="Kubernetes, Terraform"
              />
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={alignTitles}
                onChange={(event) => setAlignTitles(event.target.checked)}
              />
              <span>
                Align job titles to target role
                <em>Rewrites titles like "Developer" → "Software Engineer" using synonyms only. Won't inflate seniority.</em>
              </span>
            </label>
          </div>
          <label>
            Company/research context
            <textarea
              className="short"
              value={companyContext}
              onChange={(event) => setCompanyContext(event.target.value)}
              placeholder="Paste company tech stack notes, engineering blog notes, or Reddit ATS advice here."
            />
          </label>
          <label>
            Extra instructions
            <textarea
              className="short"
              value={extraNotes}
              onChange={(event) => setExtraNotes(event.target.value)}
            />
          </label>
          <button disabled={!canSubmit} type="submit">
            {loading ? "Rewriting..." : "Rewrite Resume"}
          </button>
          {error && <p className="error">{error}</p>}
        </section>
      </form>

      <ScreeningPanel
        jobDescription={jobDescription}
        resumeLatex={screeningResumeLatex}
        companyContext={companyContext}
        roleName={roleName}
        companyName={companyName}
      />

      {result && (
        <section className="results">
          <div className="score-card card">
            <div>
              <p className="eyebrow">Match Score</p>
              <strong>{result.match_score}%</strong>
              <span className={result.target_met ? "met" : "not-met"}>
                {result.target_met ? "Target met" : "Below target"}
              </span>
            </div>
            <div className="button-row">
              <button type="button" className="secondary" onClick={downloadTex}>
                Download .tex
              </button>
              <button type="button" onClick={copyLatex}>
                {copied ? "Copied" : "Copy LaTeX"}
              </button>
            </div>
          </div>

          <div className="result-grid">
            <section className="card output-card">
              <h2>Rewritten LaTeX</h2>
              <textarea readOnly value={result.rewritten_latex} />
            </section>
            <div className="report-stack">
              <section className="card small-card">
                <h3>PDF Compilation</h3>
                <div style={{ display: "grid", gap: "10px" }}>
                  <button 
                    type="button" 
                    onClick={handleCompile} 
                    disabled={compiling}
                    style={{ background: "#177a3d" }}
                  >
                    {compiling ? "Compiling PDF..." : "Compile LaTeX to PDF"}
                  </button>
                  
                  {compileError && (
                    <div className="error" style={{ fontSize: "14px", marginTop: "8px" }}>
                      <strong>Compile Error:</strong>
                      <pre style={{ whiteSpace: "pre-wrap", margin: "4px 0 0 0", maxHeight: "150px", overflow: "auto", fontSize: "12px", fontFamily: "monospace" }}>
                        {compileError}
                      </pre>
                    </div>
                  )}

                  {compileResult && (
                    <div style={{ fontSize: "14px", marginTop: "8px" }}>
                      {compileResult.success ? (
                        <div style={{ color: "#177a3d" }}>
                          ✓ PDF Compiled successfully! 
                          {compileResult.pdf_download_url && (
                            <a 
                              href={toAbsoluteApiUrl(compileResult.pdf_download_url)} 
                              target="_blank" 
                              rel="noreferrer"
                              style={{ display: "block", marginTop: "6px", fontWeight: "bold", color: "#5164ff" }}
                            >
                              Download PDF File
                            </a>
                          )}
                        </div>
                      ) : (
                        <div className="error">
                          <strong>Compilation Failed:</strong>
                          <ul style={{ margin: "4px 0 0 0", paddingLeft: "20px", fontSize: "12px" }}>
                            {compileResult.errors.map((err: string, i: number) => (
                              <li key={i}>{err}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </section>
              <KeywordTable
                title="Matched Keywords"
                items={result.matched_keywords}
              />
              <KeywordTable
                title="Missing Keywords"
                items={result.missing_keywords}
                onToggle={toggleMissingSkill}
                selectedItems={selectedMissingSkills}
              />
              <KeywordTable
                title="Unsupported / High Risk"
                items={result.unsupported_keywords}
                onToggle={toggleMissingSkill}
                selectedItems={selectedMissingSkills}
              />
              <section className="card small-card">
                <h3>Warnings</h3>
                {result.warnings.length ? (
                  result.warnings.map((warning) => (
                    <p key={warning} className="warning">
                      {warning}
                    </p>
                  ))
                ) : (
                  <p className="muted">None</p>
                )}
              </section>
              <section className="card small-card">
                <h3>Changes Made</h3>
                {result.changes_made.map((change) => (
                  <p key={change}>{change}</p>
                ))}
              </section>
            </div>
          </div>
        </section>
      )}

    </main>
  );
}
