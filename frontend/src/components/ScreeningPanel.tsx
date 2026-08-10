import { useState } from "react";
import { answerScreeningQuestion } from "../lib/api";

type ScreeningExchange = {
  question: string;
  answer: string;
};

export function ScreeningPanel({
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
