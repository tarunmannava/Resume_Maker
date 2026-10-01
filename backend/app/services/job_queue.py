import re
import json
import sqlite3
import threading
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

# Default path: backend/storage/jobs.db
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "storage" / "jobs.db"
_OVERRIDE_DB_PATH: Path | None = None
_lock = threading.Lock()


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed: list[str] = []

    def handle_data(self, d: str) -> None:
        self.fed.append(d)

    def get_data(self) -> str:
        return "".join(self.fed)


# Sponsorship/export-control notes usually sit at the very end of long descriptions,
# so keep the full text; the worker caps what it sends to the AI separately.
MAX_STORED_DESCRIPTION_CHARS = 50000


def clean_html_description(html_str: str) -> str:
    """Strips HTML tags and normalizes whitespace."""
    if not html_str:
        return ""
    preprocessed = re.sub(r"<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", html_str, flags=re.IGNORECASE)
    stripper = _HTMLStripper()
    try:
        stripper.feed(preprocessed)
        text = stripper.get_data()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", preprocessed)

    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text).strip()
    return text[:MAX_STORED_DESCRIPTION_CHARS]


def set_db_path(path: Path | str | None) -> None:
    """Sets a global database path override (useful for isolated tests)."""
    global _OVERRIDE_DB_PATH
    if path is None:
        _OVERRIDE_DB_PATH = None
    else:
        _OVERRIDE_DB_PATH = Path(path)


def get_db_path() -> Path:
    return _OVERRIDE_DB_PATH or DEFAULT_DB_PATH


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Initializes the SQLite schema with table and indices."""
    with _lock:
        with get_connection(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    apply_url TEXT,
                    description_text TEXT,
                    requirements_summary TEXT,
                    technical_tools TEXT,
                    yoe REAL,
                    seniority TEXT,
                    status TEXT NOT NULL DEFAULT 'queued',
                    primary_stack TEXT,
                    flag_reason TEXT,
                    screen_explanation TEXT,
                    match_score REAL,
                    docx_url TEXT,
                    error TEXT,
                    captured_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    applied_via_simplify INTEGER DEFAULT NULL,
                    skip_screening INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            # Migration: add columns missing from databases created by older versions
            cols = [col["name"] for col in conn.execute("PRAGMA table_info(jobs)").fetchall()]
            if "applied_via_simplify" not in cols:
                conn.execute("ALTER TABLE jobs ADD COLUMN applied_via_simplify INTEGER DEFAULT NULL;")
            if "skip_screening" not in cols:
                conn.execute("ALTER TABLE jobs ADD COLUMN skip_screening INTEGER NOT NULL DEFAULT 0;")

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_status_captured ON jobs(status, captured_at)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS screening_guardrails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    overlooked_text TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_guardrails_created ON screening_guardrails(created_at DESC)"
            )
            conn.commit()


def known_ids(ids: list[str], db_path: Path | None = None) -> list[str]:
    """Returns the subset of IDs that already exist in the database."""
    if not ids:
        return []
    init_db(db_path)
    with _lock:
        with get_connection(db_path) as conn:
            placeholders = ",".join("?" for _ in ids)
            rows = conn.execute(
                f"SELECT id FROM jobs WHERE id IN ({placeholders})", ids
            ).fetchall()
            return [r["id"] for r in rows]


def add_jobs(job_items: list[dict[str, Any]], db_path: Path | None = None) -> tuple[int, int]:
    """
    Inserts a batch of jobs into the database.
    Repeat captures with existing IDs are skipped.
    Returns (added_count, duplicate_count).
    """
    if not job_items:
        return 0, 0

    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    added = 0
    duplicates = 0

    with _lock:
        with get_connection(db_path) as conn:
            for item in job_items:
                job_id = str(item.get("id") or "").strip()
                if not job_id:
                    continue

                # Check if exists
                existing = conn.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
                if existing:
                    duplicates += 1
                    continue

                raw_desc = item.get("description_text") or item.get("description") or item.get("jd") or ""
                cleaned_desc = clean_html_description(raw_desc)

                tools = item.get("technical_tools") or []
                if isinstance(tools, (list, tuple)):
                    tools_json = json.dumps(tools)
                elif isinstance(tools, str):
                    tools_json = tools
                else:
                    tools_json = "[]"

                conn.execute(
                    """
                    INSERT INTO jobs (
                        id, title, company, location, apply_url, description_text,
                        requirements_summary, technical_tools, yoe, seniority,
                        status, primary_stack, flag_reason, screen_explanation,
                        match_score, docx_url, error, captured_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', NULL, NULL, NULL, NULL, NULL, NULL, ?, ?)
                    """,
                    (
                        job_id,
                        item.get("title") or "Unknown Role",
                        item.get("company") or "Unknown Company",
                        item.get("location") or "United States",
                        item.get("apply_url") or "",
                        cleaned_desc,
                        item.get("requirements_summary") or "",
                        tools_json,
                        item.get("yoe"),
                        item.get("seniority") or "",
                        now_iso,
                        now_iso,
                    ),
                )
                added += 1

            conn.commit()

    return added, duplicates


def claim_next(db_path: Path | None = None) -> dict[str, Any] | None:
    """
    Atomically claims the next oldest 'queued' job by setting its status to 'screening'.
    Returns the job dict or None if no queued job exists.
    """
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    with _lock:
        with get_connection(db_path) as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE status = 'queued' ORDER BY captured_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None

            job_id = row["id"]
            conn.execute(
                "UPDATE jobs SET status = 'screening', updated_at = ? WHERE id = ?",
                (now_iso, job_id),
            )
            conn.commit()

            updated = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return dict(updated) if updated else None


def update_job(job_id: str, db_path: Path | None = None, **fields: Any) -> bool:
    """Updates fields on an existing job and stamps updated_at."""
    if not fields:
        return False

    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    fields["updated_at"] = now_iso

    keys = list(fields.keys())
    values = list(fields.values())
    set_clause = ", ".join(f"{k} = ?" for k in keys)
    values.append(job_id)

    with _lock:
        with get_connection(db_path) as conn:
            cursor = conn.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0


def requeue_interrupted(db_path: Path | None = None) -> int:
    """
    Resets any in-flight jobs ('screening' or 'rewriting') back to 'queued' on startup.
    Returns the count of requeued jobs.
    """
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    with _lock:
        with get_connection(db_path) as conn:
            cursor = conn.execute(
                "UPDATE jobs SET status = 'queued', updated_at = ? WHERE status IN ('screening', 'rewriting')",
                (now_iso,),
            )
            conn.commit()
            return cursor.rowcount


def list_jobs(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Lists jobs sorted by captured_at descending, optionally filtered by status.
    `status` may be a comma-separated list, e.g. 'queued,screening,rewriting'.
    """
    init_db(db_path)
    statuses = [s.strip().lower() for s in (status or "").split(",") if s.strip()]
    with _lock:
        with get_connection(db_path) as conn:
            if statuses and "all" not in statuses:
                placeholders = ",".join("?" for _ in statuses)
                rows = conn.execute(
                    f"SELECT * FROM jobs WHERE status IN ({placeholders}) ORDER BY captured_at DESC LIMIT ? OFFSET ?",
                    (*statuses, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY captured_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()

            res: list[dict[str, Any]] = []
            for r in rows:
                d = dict(r)
                if d.get("technical_tools"):
                    try:
                        d["technical_tools"] = json.loads(d["technical_tools"])
                    except Exception:
                        pass
                if "applied_via_simplify" in d and d["applied_via_simplify"] is not None:
                    d["applied_via_simplify"] = bool(d["applied_via_simplify"])
                res.append(d)
            return res


def get_job(job_id: str, db_path: Path | None = None) -> dict[str, Any] | None:
    """Retrieves a single job by its ID."""
    init_db(db_path)
    with _lock:
        with get_connection(db_path) as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get("technical_tools"):
                try:
                    d["technical_tools"] = json.loads(d["technical_tools"])
                except Exception:
                    pass
            if "applied_via_simplify" in d and d["applied_via_simplify"] is not None:
                d["applied_via_simplify"] = bool(d["applied_via_simplify"])
            return d


def stats(db_path: Path | None = None) -> dict[str, int]:
    """Returns job counts grouped by status."""
    init_db(db_path)
    with _lock:
        with get_connection(db_path) as conn:
            rows = conn.execute("SELECT status, count(*) as count FROM jobs GROUP BY status").fetchall()
            res = {
                "queued": 0,
                "screening": 0,
                "rewriting": 0,
                "ready": 0,
                "low_match": 0,
                "flagged": 0,
                "rejected": 0,
                "failed": 0,
                "applied": 0,
                "dismissed": 0,
                "total": 0,
            }
            total = 0
            for r in rows:
                st = r["status"]
                cnt = r["count"]
                res[st] = cnt
                total += cnt
            res["total"] = total
            return res


def retry_job(job_id: str, force: bool = False, db_path: Path | None = None) -> bool:
    """
    Requeues a failed or flagged job.
    If force=True (e.g. rewrite anyway for a flagged job), the worker skips AI screening
    so the job goes straight to rewriting instead of being flagged again.
    """
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    with _lock:
        with get_connection(db_path) as conn:
            row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return False

            if force:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = 'queued', flag_reason = NULL, error = NULL, skip_screening = 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (now_iso, job_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = 'queued', error = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (now_iso, job_id),
                )
            conn.commit()
            return True


def set_job_status(
    job_id: str,
    status: str,
    db_path: Path | None = None,
    applied_via_simplify: bool | None = None,
    flag_reason: str | None = None,
    screen_explanation: str | None = None,
) -> bool:
    """Directly sets status to 'applied', 'dismissed', 'flagged', etc.
    When status is 'applied', applied_via_simplify defaults to False (0, Tailored) unless explicitly enabled.
    When status is 'flagged', flag_reason and screen_explanation can be set.
    """
    valid_statuses = {
        "queued",
        "screening",
        "rewriting",
        "ready",
        "low_match",
        "flagged",
        "rejected",
        "failed",
        "applied",
        "dismissed",
    }
    st_clean = status.lower().strip()
    if st_clean not in valid_statuses:
        return False

    fields: dict[str, Any] = {"status": st_clean}
    if flag_reason is not None:
        fields["flag_reason"] = flag_reason
    if screen_explanation is not None:
        fields["screen_explanation"] = screen_explanation
    if st_clean == "applied":
        # Default to 0 (Tailored resume, toggle disabled) unless explicitly True
        is_simplify = bool(applied_via_simplify) if applied_via_simplify is not None else False
        fields["applied_via_simplify"] = 1 if is_simplify else 0
    elif applied_via_simplify is not None:
        fields["applied_via_simplify"] = 1 if applied_via_simplify else 0

    return update_job(job_id, db_path=db_path, **fields)


def toggle_job_simplify(
    job_id: str,
    applied_via_simplify: bool,
    db_path: Path | None = None,
) -> bool:
    """Toggles whether an applied job was submitted via Simplify / Original resume or Tailored resume."""
    return update_job(
        job_id,
        db_path=db_path,
        applied_via_simplify=1 if applied_via_simplify else 0,
    )


def add_screening_guardrail(
    job_id: str,
    reason: str,
    overlooked_text: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Adds a human feedback guardrail entry and sets the job to 'flagged'."""
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_reason = reason.strip() or "Security Clearance"
    clean_snippet = overlooked_text.strip() if overlooked_text else None
    explanation = (
        f"Flagged by user (Golden guardrail): {clean_snippet}"
        if clean_snippet
        else f"Flagged by user (Golden guardrail): {clean_reason}"
    )

    with _lock:
        with get_connection(db_path) as conn:
            job_row = conn.execute("SELECT title, company FROM jobs WHERE id = ?", (job_id,)).fetchone()
            job_title = job_row["title"] if job_row else "Unknown Title"
            company = job_row["company"] if job_row else "Unknown Company"

            cursor = conn.execute(
                """
                INSERT INTO screening_guardrails (job_id, job_title, company, reason, overlooked_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, job_title, company, clean_reason, clean_snippet, now_iso),
            )
            guardrail_id = cursor.lastrowid

            # Update the job status to flagged
            conn.execute(
                """
                UPDATE jobs
                SET status = 'flagged', flag_reason = ?, screen_explanation = ?, updated_at = ?
                WHERE id = ?
                """,
                (clean_reason, explanation, now_iso, job_id),
            )
            conn.commit()

            return {
                "id": guardrail_id,
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "reason": clean_reason,
                "overlooked_text": clean_snippet,
                "created_at": now_iso,
            }


def get_screening_guardrails(limit: int = 50, db_path: Path | None = None) -> list[dict[str, Any]]:
    """Returns stored golden guardrails sorted by creation date descending."""
    init_db(db_path)
    with _lock:
        with get_connection(db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM screening_guardrails ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

