import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import {
  healthCheck,
  rewriteResume,
  analyzeJob,
  compileLatex,
  compileDocx,
  toAbsoluteApiUrl,
  answerScreeningQuestion,
} from "./lib/api";
import type {
  KeywordMatch,
  RewriteMode,
  RewriteResponse,
  CompileResponse,
} from "./lib/api";
import { sampleResume } from "./lib/constants";
import "./styles.css";

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
  const [selectedRoleCategory, setSelectedRoleCategory] = useState("Java Developer");
  const [selectedStackOverride, setSelectedStackOverride] = useState<
    "auto" | "dotnet" | "java" | "node" | "python" | "ai"
  >("auto");
  const [detectedIndustry, setDetectedIndustry] = useState<string | null>(null);
  const [detectedRoleCategory, setDetectedRoleCategory] = useState<string | null>(null);
  const [showIndustryWarning, setShowIndustryWarning] = useState(false);
  const [analyzingJob, setAnalyzingJob] = useState(false);
  const [compiling, setCompiling] = useState(false);
  const [compileResult, setCompileResult] = useState<CompileResponse | null>(null);
  const [compileError, setCompileError] = useState<string | null>(null);
  const [exportingDocx, setExportingDocx] = useState(false);
  const [docxResult, setDocxResult] = useState<CompileResponse | null>(null);
  const [docxError, setDocxError] = useState<string | null>(null);
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

  async function handleExportDocx() {
    if (!result?.rewritten_latex) return;
    setExportingDocx(true);
    setDocxError(null);
    try {
      const res = await compileDocx({
        latex_code: result.rewritten_latex,
        candidate_name: candidateName || "Resume",
        company_name: companyName || "General",
        role_name: roleName || "Position",
      });
      setDocxResult(res);
      if (res.success && res.docx_download_url) {
        const link = document.createElement("a");
        link.href = toAbsoluteApiUrl(res.docx_download_url);
        link.download = `${res.filename_base || "Resume"}.docx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else if (!res.success) {
        setDocxError(res.errors.join("\n") || "Failed to generate DOCX");
      }
    } catch (caught) {
      setDocxError(caught instanceof Error ? caught.message : "DOCX export error");
    } finally {
      setExportingDocx(false);
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
        selected_stack_override: selectedStackOverride === "auto" ? null : selectedStackOverride,
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
        <div className="hero-copy">
          <p className="eyebrow">Resume Maker · ATS workspace</p>
          <h1>Turn a job description into a stronger, honest resume.</h1>
          <p>
            Add the role and your LaTeX source, then rewrite, review the fit, and export when everything looks right.
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

      <div className="workflow-bar" aria-label="Resume workflow">
        <div className={`workflow-step active`}>
          <span>01</span>
          <div><strong>Prepare</strong><small>Job + resume</small></div>
        </div>
        <div className={`workflow-line ${result ? "complete" : ""}`} />
        <div className={`workflow-step ${result ? "active" : ""}`}>
          <span>02</span>
          <div><strong>Rewrite</strong><small>Evidence-led edits</small></div>
        </div>
        <div className={`workflow-line ${result ? "complete" : ""}`} />
        <div className={`workflow-step ${result ? "active" : ""}`}>
          <span>03</span>
          <div><strong>Review</strong><small>ATS fit + export</small></div>
        </div>
      </div>

      <form className="workspace" onSubmit={handleSubmit}>
        <div className="editor-grid">
        <section className="card editor-card job-editor">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Step 1</span>
              <h2>Job description</h2>
            </div>
            <div className="editor-tools">
              <button
                type="button"
                className="secondary"
                style={{ padding: "6px 12px", borderRadius: "8px", fontSize: "12px" }}
                onClick={handleAnalyzeJob}
                disabled={jobDescription.length < 20 || analyzingJob}
              >
                {analyzingJob ? "Analyzing..." : "Detect Role & Industry"}
              </button>
              <span className="editor-count">{jobDescription.length.toLocaleString()} chars</span>
            </div>
          </div>
          <textarea
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            onBlur={handleAnalyzeJob}
            placeholder="Paste the job description here..."
          />
        </section>

        <section className="card editor-card resume-editor">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Step 2</span>
              <h2>Current LaTeX resume</h2>
            </div>
            <span className="editor-count">{resumeLatex.length.toLocaleString()} chars</span>
          </div>
          <textarea
            value={resumeLatex}
            onChange={(event) => setResumeLatex(event.target.value)}
          />
        </section>
        </div>

        <section className="card settings-card">
          <div className="settings-header">
            <div>
              <span className="section-kicker">Controls</span>
              <h2>Rewrite settings</h2>
            </div>
            <p className="muted">Keep the defaults, or tune the rewrite for a specific application.</p>
          </div>

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
              Target Role Focus
              <select
                value={selectedRoleCategory}
                onChange={(event) => setSelectedRoleCategory(event.target.value)}
              >
                <option value="Java Developer">Java Developer</option>
                <option value="AI Engineer / Software Engineer">AI Engineer / Software Engineer</option>
              </select>
            </label>
            <label style={{ gridColumn: "span 2" }}>
              Target Tech Stack Override
              <div style={{ display: "flex", gap: "8px", marginTop: "4px", flexWrap: "wrap" }}>
                {(["auto", "dotnet", "java", "node", "python", "ai"] as const).map((stack) => (
                  <button
                    key={stack}
                    type="button"
                    className={selectedStackOverride === stack ? "primary" : "secondary"}
                    style={{
                      padding: "4px 12px",
                      borderRadius: "6px",
                      fontSize: "12px",
                    }}
                    onClick={() => setSelectedStackOverride(stack)}
                  >
                    {stack === "auto"
                      ? "⚡ Auto-Detect"
                      : stack === "dotnet"
                      ? ".NET / C#"
                      : stack === "java"
                      ? "Java / Spring"
                      : stack === "node"
                      ? "Node / React"
                      : stack === "ai"
                      ? "AI / ML"
                      : "Python / FastAPI"}
                  </button>
                ))}
              </div>
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
          <div className="submit-row">
            <div>
              <strong>{loading ? "Working on your resume…" : "Ready to rewrite?"}</strong>
              <span className="muted">The original document stays unchanged until you review the result.</span>
            </div>
            <button className="primary-action" disabled={!canSubmit} type="submit">
              {loading ? "Rewriting…" : "Rewrite resume"}
              <span aria-hidden="true">→</span>
            </button>
          </div>
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
              <button
                type="button"
                style={{ background: "#2563eb", color: "#fff", fontWeight: 600 }}
                onClick={handleExportDocx}
                disabled={exportingDocx}
              >
                {exportingDocx ? "Exporting DOCX..." : "📝 Download Word (.docx)"}
              </button>
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
                <h3>Document Export</h3>
                <div style={{ display: "grid", gap: "12px" }}>
                  {/* DOCX Export Button */}
                  <div>
                    <button 
                      type="button" 
                      onClick={handleExportDocx} 
                      disabled={exportingDocx}
                      style={{ background: "#2563eb", width: "100%", fontWeight: 600 }}
                    >
                      {exportingDocx ? "Exporting DOCX..." : "📝 Export & Download Word (.docx)"}
                    </button>
                    {docxError && (
                      <div className="error" style={{ fontSize: "13px", marginTop: "6px" }}>
                        <strong>DOCX Error:</strong> {docxError}
                      </div>
                    )}
                    {docxResult?.success && docxResult.docx_download_url && (
                      <div style={{ color: "#177a3d", fontSize: "13px", marginTop: "6px" }}>
                        ✓ DOCX generated! <a href={toAbsoluteApiUrl(docxResult.docx_download_url)} download={`${docxResult.filename_base || "Resume"}.docx`} style={{ fontWeight: "bold", color: "#2563eb" }}>Click here to re-download</a>
                      </div>
                    )}
                  </div>

                  <hr style={{ border: 0, borderTop: "1px solid #333", margin: "4px 0" }} />

                  {/* PDF Compile Button */}
                  <div>
                    <button 
                      type="button" 
                      onClick={handleCompile} 
                      disabled={compiling}
                      style={{ background: "#177a3d", width: "100%" }}
                    >
                      {compiling ? "Compiling PDF..." : "📄 Compile LaTeX to PDF"}
                    </button>
                    
                    {compileError && (
                      <div className="error" style={{ fontSize: "13px", marginTop: "6px" }}>
                        <strong>Compile Error:</strong>
                        <pre style={{ whiteSpace: "pre-wrap", margin: "4px 0 0 0", maxHeight: "150px", overflow: "auto", fontSize: "12px", fontFamily: "monospace" }}>
                          {compileError}
                        </pre>
                      </div>
                    )}

                    {compileResult && (
                      <div style={{ fontSize: "13px", marginTop: "6px" }}>
                        {compileResult.success && compileResult.pdf_download_url ? (
                          <div style={{ color: "#177a3d" }}>
                            ✓ PDF Compiled! <a href={toAbsoluteApiUrl(compileResult.pdf_download_url)} target="_blank" rel="noreferrer" style={{ fontWeight: "bold", color: "#5164ff" }}>Open / Download PDF</a>
                          </div>
                        ) : null}
                      </div>
                    )}
                  </div>
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
