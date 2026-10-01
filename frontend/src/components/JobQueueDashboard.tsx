import React, { useEffect, useState, useCallback } from "react";
import {
  fetchQueueJobs,
  fetchQueueStats,
  updateQueueJobStatus,
  toggleQueueJobSimplify,
  retryQueueJob,
  flagJobWithGuardrail,
  toAbsoluteApiUrl,
} from "../lib/api";
import type { QueueJob, QueueStats } from "../lib/api";

interface JobQueueDashboardProps {
  onOpenInStudio?: (job: QueueJob) => void;
}

export function JobQueueDashboard({ onOpenInStudio }: JobQueueDashboardProps = {}) {
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [jobs, setJobs] = useState<QueueJob[]>([]);
  const [activeTab, setActiveTab] = useState<string>("ready");
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Golden Guardrail Flag Modal State
  const [flagModalJob, setFlagModalJob] = useState<QueueJob | null>(null);
  const [flagReason, setFlagReason] = useState<string>("Security Clearance");
  const [customReason, setCustomReason] = useState<string>("");
  const [overlookedSnippet, setOverlookedSnippet] = useState<string>("");
  const [flagSuccessMsg, setFlagSuccessMsg] = useState<string | null>(null);
  const [isSubmittingGuardrail, setIsSubmittingGuardrail] = useState<boolean>(false);

  const loadData = useCallback(async (tabToLoad: string = activeTab) => {
    try {
      const [newStats, newJobs] = await Promise.all([
        fetchQueueStats(),
        fetchQueueJobs(tabToLoad === "processing" ? "queued,screening,rewriting" : tabToLoad),
      ]);
      setStats(newStats);
      setJobs(newJobs);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed loading job queue");
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadData(activeTab);
    const interval = setInterval(() => {
      loadData(activeTab);
    }, 5000);
    return () => clearInterval(interval);
  }, [loadData, activeTab]);

  const handleStatusChange = async (jobId: string, status: string, appliedViaSimplify?: boolean) => {
    try {
      setActionLoading(jobId);
      await updateQueueJobStatus(jobId, status, appliedViaSimplify);
      await loadData();
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleSimplify = async (jobId: string, appliedViaSimplify: boolean) => {
    try {
      setActionLoading(jobId);
      await toggleQueueJobSimplify(jobId, appliedViaSimplify);
      await loadData();
    } catch (err: any) {
      alert(`Toggle failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetry = async (jobId: string, force: boolean = false) => {
    try {
      setActionLoading(jobId);
      await retryQueueJob(jobId, force);
      await loadData();
    } catch (err: any) {
      alert(`Retry failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const openFlagModal = (job: QueueJob, defaultReason: string = "Security Clearance") => {
    setFlagModalJob(job);
    setFlagReason(defaultReason);
    setCustomReason("");
    setOverlookedSnippet("");
  };

  const closeFlagModal = () => {
    setFlagModalJob(null);
    setCustomReason("");
    setOverlookedSnippet("");
  };

  const handleConfirmFlagGuardrail = async () => {
    if (!flagModalJob) return;
    const finalReason = flagReason === "Other" ? (customReason.trim() || "Ineligible") : flagReason;
    try {
      setIsSubmittingGuardrail(true);
      await flagJobWithGuardrail(flagModalJob.id, finalReason, overlookedSnippet.trim() || undefined);
      setFlagSuccessMsg(`Job flagged as "${finalReason}" and saved to Golden Guardrails dataset.`);
      setTimeout(() => setFlagSuccessMsg(null), 5000);
      closeFlagModal();
      await loadData();
    } catch (err: any) {
      alert(`Flagging failed: ${err.message}`);
    } finally {
      setIsSubmittingGuardrail(false);
    }
  };

  const getStatusBadge = (status: string, job?: QueueJob) => {
    switch (status) {
      case "ready":
        return <span className="queue-badge ready">Ready</span>;
      case "low_match":
        return <span className="queue-badge low-match">Low Match (&lt;70%)</span>;
      case "flagged":
        return <span className="queue-badge flagged">Flagged</span>;
      case "screening":
        return <span className="queue-badge processing">Screening...</span>;
      case "rewriting":
        return <span className="queue-badge processing">Rewriting...</span>;
      case "queued":
        return <span className="queue-badge queued">Queued</span>;
      case "applied":
        return (
          <span
            className={`queue-badge applied ${
              Boolean(job?.applied_via_simplify) ? "applied-simplify" : "applied-tailored"
            }`}
          >
            {Boolean(job?.applied_via_simplify) ? "⚡ Applied • Simplify" : "📄 Applied • Tailored"}
          </span>
        );
      case "failed":
        return <span className="queue-badge failed">Failed</span>;
      case "dismissed":
        return <span className="queue-badge dismissed">Dismissed</span>;
      default:
        return <span className="queue-badge">{status}</span>;
    }
  };

  const getStackBadge = (stack?: string | null) => {
    if (!stack) return null;
    const clean = stack.toLowerCase();
    return <span className={`stack-tag stack-${clean}`}>{clean.toUpperCase()}</span>;
  };

  return (
    <div className="queue-dashboard">
      {/* Header Summary Cards */}
      <div className="queue-summary-grid">
        <div
          className={`summary-card ${activeTab === "ready" ? "active" : ""}`}
          onClick={() => setActiveTab("ready")}
        >
          <div className="summary-label">Ready to Apply</div>
          <div className="summary-val text-ready">{stats?.ready ?? 0}</div>
          <div className="summary-sub">&ge;70% Match &amp; Compiled</div>
        </div>

        <div
          className={`summary-card ${activeTab === "low_match" ? "active" : ""}`}
          onClick={() => setActiveTab("low_match")}
        >
          <div className="summary-label">Low Match (&lt;70%)</div>
          <div className="summary-val text-low-match">{stats?.low_match ?? 0}</div>
          <div className="summary-sub">Under 70% threshold</div>
        </div>

        <div
          className={`summary-card ${activeTab === "flagged" ? "active" : ""}`}
          onClick={() => setActiveTab("flagged")}
        >
          <div className="summary-label">Flagged by AI</div>
          <div className="summary-val text-flagged">{stats?.flagged ?? 0}</div>
          <div className="summary-sub">Internship / Clearance / Sponsorship / C++</div>
        </div>

        <div
          className={`summary-card ${activeTab === "processing" ? "active" : ""}`}
          onClick={() => setActiveTab("processing")}
        >
          <div className="summary-label">In Pipeline</div>
          <div className="summary-val text-processing">
            {(stats?.queued ?? 0) + (stats?.screening ?? 0) + (stats?.rewriting ?? 0)}
          </div>
          <div className="summary-sub">
            {stats?.screening ? "Screening 1 job" : stats?.rewriting ? "Rewriting 1 job" : "Idle"}
          </div>
        </div>

        <div
          className={`summary-card ${activeTab === "applied" ? "active" : ""}`}
          onClick={() => setActiveTab("applied")}
        >
          <div className="summary-label">Applied</div>
          <div className="summary-val text-applied">{stats?.applied ?? 0}</div>
          <div className="summary-sub">Tracked submissions</div>
        </div>

        <div
          className={`summary-card ${activeTab === "failed" ? "active" : ""}`}
          onClick={() => setActiveTab("failed")}
        >
          <div className="summary-label">Failed</div>
          <div className="summary-val text-failed">{stats?.failed ?? 0}</div>
          <div className="summary-sub">Errors needing retry</div>
        </div>
      </div>

      {/* Tabs bar & Controls */}
      <div className="queue-controls-bar">
        <div className="queue-tabs">
          <button
            className={`queue-tab ${activeTab === "ready" ? "active" : ""}`}
            onClick={() => setActiveTab("ready")}
          >
            Ready ({stats?.ready ?? 0})
          </button>
          <button
            className={`queue-tab ${activeTab === "low_match" ? "active" : ""}`}
            onClick={() => setActiveTab("low_match")}
          >
            Low Match ({stats?.low_match ?? 0})
          </button>
          <button
            className={`queue-tab ${activeTab === "flagged" ? "active" : ""}`}
            onClick={() => setActiveTab("flagged")}
          >
            Flagged ({stats?.flagged ?? 0})
          </button>
          <button
            className={`queue-tab ${activeTab === "processing" ? "active" : ""}`}
            onClick={() => setActiveTab("processing")}
          >
            In Progress ({(stats?.queued ?? 0) + (stats?.screening ?? 0) + (stats?.rewriting ?? 0)})
          </button>
          <button
            className={`queue-tab ${activeTab === "applied" ? "active" : ""}`}
            onClick={() => setActiveTab("applied")}
          >
            Applied ({stats?.applied ?? 0})
          </button>
          <button
            className={`queue-tab ${activeTab === "all" ? "active" : ""}`}
            onClick={() => setActiveTab("all")}
          >
            All ({stats?.total ?? 0})
          </button>
        </div>

        <div className="queue-right-actions">
          <button className="btn-secondary small" onClick={() => loadData(activeTab)}>
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="queue-error-banner">{error}</div>}
      {flagSuccessMsg && <div className="queue-success-banner">{flagSuccessMsg}</div>}

      {/* Jobs List */}
      {loading && !jobs.length ? (
        <div className="queue-loading">Loading jobs queue...</div>
      ) : jobs.length === 0 ? (
        <div className="queue-empty">
          <p>No jobs found in tab "{activeTab.toUpperCase()}".</p>
          <span className="muted">
            Open HiringCafe in Chrome, navigate to your saved search, and click "Capture This Page" in the extension popup.
          </span>
        </div>
      ) : (
        <div className="queue-list">
          {jobs.map((job) => {
            const isLoading = actionLoading === job.id;
            return (
              <div className={`queue-card status-${job.status}`} key={job.id}>
                <div className="queue-card-header">
                  <div className="queue-card-title-group">
                    <h3 className="queue-job-title">{job.title}</h3>
                    <div className="queue-job-meta">
                      <span className="queue-company">{job.company}</span>
                      {job.location && <span className="queue-sep">•</span>}
                      {job.location && <span className="queue-loc">{job.location}</span>}
                      {job.yoe !== null && job.yoe !== undefined && (
                        <>
                          <span className="queue-sep">•</span>
                          <span className="queue-yoe">{job.yoe} YOE</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="queue-card-badges">
                    {getStackBadge(job.primary_stack)}
                    {getStatusBadge(job.status, job)}
                    {job.match_score != null && (
                      <span className={`match-pill ${job.match_score < 70 ? "match-low" : ""}`}>
                        {Math.round(job.match_score)}% Match
                      </span>
                    )}
                  </div>
                </div>

                {/* Flagged Reason Box */}
                {job.status === "flagged" && (
                  <div className="queue-alert-box flagged-box">
                    <div className="alert-head">
                      <strong>AI Flag: {job.flag_reason || "Disqualified"}</strong>
                    </div>
                    {job.screen_explanation && (
                      <div className="alert-text">{job.screen_explanation}</div>
                    )}
                  </div>
                )}

                {/* Error Box */}
                {job.status === "failed" && job.error && (
                  <div className="queue-alert-box error-box">
                    <strong>Error:</strong> {job.error}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="queue-card-actions">
                  {(job.status === "ready" || job.status === "low_match") && job.docx_url && (
                    <a
                      href={toAbsoluteApiUrl(job.docx_url)}
                      download
                      className="btn-primary-action"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Download DOCX
                    </a>
                  )}

                  {job.apply_url && (
                    <a
                      href={job.apply_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-outline-action"
                    >
                      Apply Link &rarr;
                    </a>
                  )}

                  {onOpenInStudio && Boolean(job.description_text) && (
                    <button
                      type="button"
                      className="btn-outline-action"
                      onClick={() => onOpenInStudio(job)}
                      title="Load this job description into Manual Rewriter Studio"
                    >
                      Studio &rarr;
                    </button>
                  )}

                  {job.status === "ready" && (
                    <>
                      <button
                        type="button"
                        className="btn-flag-clearance"
                        disabled={isLoading}
                        onClick={() => openFlagModal(job, "Security Clearance")}
                        title="Flag this job and save the overlooked reason as a Golden Guardrail"
                      >
                        🚩 Flag (Guardrail)
                      </button>
                      <button
                        type="button"
                        className="btn-outline-action"
                        disabled={isLoading}
                        onClick={() => handleRetry(job.id, true)}
                        title="Rewrite this job again with the same stack (screening is skipped)"
                      >
                        🔄 Retry
                      </button>
                      <button
                        className="btn-text-action"
                        disabled={isLoading}
                        onClick={() => handleStatusChange(job.id, "applied", false)}
                        title="Mark applied (defaults to Tailored resume, toggle disabled)"
                      >
                        Mark Applied
                      </button>
                    </>
                  )}

                  {job.status === "low_match" && (
                    <>
                      <button
                        type="button"
                        className="btn-flag-clearance"
                        disabled={isLoading}
                        onClick={() => openFlagModal(job, "Security Clearance")}
                        title="Flag this job and save the overlooked reason as a Golden Guardrail"
                      >
                        🚩 Flag (Guardrail)
                      </button>
                      <button
                        type="button"
                        className="btn-outline-action"
                        disabled={isLoading}
                        onClick={() => handleRetry(job.id, true)}
                        title="Rewrite this job again with the same stack"
                      >
                        🔄 Retry
                      </button>
                      <button
                        className="btn-text-action"
                        disabled={isLoading}
                        onClick={() => handleStatusChange(job.id, "applied", false)}
                        title="Mark applied despite low match score"
                      >
                        Mark Applied
                      </button>
                    </>
                  )}

                  {job.status === "applied" && (
                    <>
                      <button
                        type="button"
                        className={`btn-simplify-toggle ${Boolean(job.applied_via_simplify) ? "simplify" : "tailored"}`}
                        disabled={isLoading}
                        onClick={() => handleToggleSimplify(job.id, !Boolean(job.applied_via_simplify))}
                        title={
                          Boolean(job.applied_via_simplify)
                            ? "Simplify toggle enabled (1). Click to disable and mark as Tailored (0)."
                            : "Tailored by default (0). Click to enable Simplify toggle (1)."
                        }
                      >
                        {Boolean(job.applied_via_simplify) ? "⚡ Simplify: ON" : "📄 Simplify: OFF (Tailored)"}
                      </button>
                      <button
                        type="button"
                        className="btn-flag-clearance"
                        disabled={isLoading}
                        onClick={() => openFlagModal(job, "Security Clearance")}
                        title="Flag this job and save the overlooked reason as a Golden Guardrail"
                      >
                        🚩 Flag (Guardrail)
                      </button>
                      <button
                        type="button"
                        className="btn-text-action muted-action"
                        disabled={isLoading}
                        onClick={() => handleStatusChange(job.id, "ready")}
                        title="Move back to Ready"
                      >
                        Unmark
                      </button>
                    </>
                  )}

                  {job.status === "flagged" && (
                    <button
                      className="btn-primary-action small"
                      disabled={isLoading}
                      onClick={() => handleRetry(job.id, true)}
                    >
                      ⚡ Rewrite Anyway
                    </button>
                  )}

                  {job.status === "failed" && (
                    <button
                      className="btn-primary-action small"
                      disabled={isLoading}
                      onClick={() => handleRetry(job.id, false)}
                    >
                      Retry
                    </button>
                  )}

                  {job.status !== "dismissed" && job.status !== "applied" && (
                    <button
                      className="btn-text-action muted-action"
                      disabled={isLoading}
                      onClick={() => handleStatusChange(job.id, "dismissed")}
                    >
                      Dismiss
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Golden Guardrail Flag Modal */}
      {flagModalJob && (
        <div className="guardrail-modal-overlay" onClick={closeFlagModal}>
          <div className="guardrail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="guardrail-modal-header">
              <div className="modal-title-wrap">
                <span className="modal-icon">🚩</span>
                <div>
                  <h3 className="modal-title">Flag Job &amp; Add Golden Guardrail</h3>
                  <div className="modal-subtitle">
                    {flagModalJob.title} • {flagModalJob.company}
                  </div>
                </div>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={closeFlagModal}
                disabled={isSubmittingGuardrail}
              >
                ✕
              </button>
            </div>

            <div className="guardrail-modal-body">
              <p className="guardrail-intro-text">
                Flagging this position marks it as disqualified and saves your correction as a{" "}
                <strong>Golden Guardrail</strong>. The AI classifier will use this example in future screenings to avoid making the same mistake.
              </p>

              <div className="form-group">
                <label className="form-label">Disqualification Reason:</label>
                <div className="reason-pills-grid">
                  {[
                    "Security Clearance",
                    "U.S. Citizenship Required",
                    "No Visa Sponsorship",
                    "Excessive Seniority / 5+ YOE",
                    "Pure C++ / Hardware / Embedded",
                    "Other",
                  ].map((r) => (
                    <button
                      key={r}
                      type="button"
                      className={`reason-pill ${flagReason === r ? "active" : ""}`}
                      onClick={() => setFlagReason(r)}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>

              {flagReason === "Other" && (
                <div className="form-group">
                  <label className="form-label">Specify Custom Reason:</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Master's Degree Required, Onsite Only in SF"
                    value={customReason}
                    onChange={(e) => setCustomReason(e.target.value)}
                  />
                </div>
              )}

              <div className="form-group">
                <label className="form-label">
                  Overlooked Requirement / Snippet from Job Description (Optional):
                </label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder='e.g. "Candidate must hold an active Secret clearance or be eligible to obtain Public Trust within 6 months."'
                  value={overlookedSnippet}
                  onChange={(e) => setOverlookedSnippet(e.target.value)}
                />
                <span className="form-hint">
                  💡 Pasting the overlooked sentence allows the system to build exact matching guardrails and few-shot examples for future AI prompts.
                </span>
              </div>
            </div>

            <div className="guardrail-modal-footer">
              <button
                type="button"
                className="btn-secondary"
                onClick={closeFlagModal}
                disabled={isSubmittingGuardrail}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-danger-confirm"
                onClick={handleConfirmFlagGuardrail}
                disabled={isSubmittingGuardrail}
              >
                {isSubmittingGuardrail ? "Saving Guardrail..." : "Confirm & Add Golden Guardrail"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
