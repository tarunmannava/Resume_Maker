import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

class CompileResponse(BaseModel):
    success: bool
    filename_base: str
    tex_path: str | None = None
    pdf_path: str | None = None
    docx_path: str | None = None
    docx_download_url: str | None = None
    log_path: str | None = None
    pdf_download_url: str | None = None
    compiler: str | None = None
    errors: list[str] = []
    warnings: list[str] = []

BACKEND_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOT = BACKEND_ROOT / "storage" / "generated"
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def sanitize_filename_part(value: str, default: str = "", max_length: int = 255) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = default
    if cleaned.upper() in WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned}_File"
    return cleaned[:max_length]


def build_filename_base(candidate_name: str, company_name: str = "", role_name: str = "") -> str:
    cand = sanitize_filename_part(candidate_name, default="TarunMannava")
    comp = sanitize_filename_part(company_name, default="")
    role = sanitize_filename_part(role_name, default="SoftwareEngineer")
    if comp:
        return f"{cand}_{comp}_{role}"
    return f"{cand}_{role}"


def safe_relative(path: Path) -> str:
    try:
        return str(path.relative_to(BACKEND_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def compiler_available(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(
    command: list[str], cwd: Path, timeout_seconds: int
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def compile_latex_to_pdf(
    latex_code: str,
    candidate_name: str,
    company_name: str,
    role_name: str,
    *,
    timeout_seconds: int = 90,
) -> CompileResponse:
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    filename_base = build_filename_base(candidate_name, company_name, role_name)
    output_dir = GENERATED_ROOT / filename_base
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_path = output_dir / f"{filename_base}.tex"
    pdf_path = output_dir / f"{filename_base}.pdf"
    log_path = output_dir / f"{filename_base}.log"
    tex_path.write_text(latex_code, encoding="utf-8")

    errors: list[str] = []
    warnings: list[str] = []
    compiler: str | None = None

    try:
        if compiler_available("latexmk") and compiler_available("perl"):
            compiler = "latexmk"
            result = run_command(
                [
                    "latexmk",
                    "-pdf",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    "-synctex=0",
                    tex_path.name,
                ],
                cwd=output_dir,
                timeout_seconds=timeout_seconds,
            )
        elif compiler_available("pdflatex"):
            compiler = "pdflatex"
            first = run_command(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    tex_path.name,
                ],
                cwd=output_dir,
                timeout_seconds=timeout_seconds,
            )
            second = run_command(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    tex_path.name,
                ],
                cwd=output_dir,
                timeout_seconds=timeout_seconds,
            )
            result = second if first.returncode == 0 else first
        else:
            return CompileResponse(
                success=False,
                filename_base=filename_base,
                tex_path=safe_relative(tex_path),
                errors=[
                    "No LaTeX compiler found. Install MiKTeX or TeX Live and ensure latexmk or pdflatex is on PATH."
                ],
            )
    except subprocess.TimeoutExpired:
        return CompileResponse(
            success=False,
            filename_base=filename_base,
            tex_path=safe_relative(tex_path),
            log_path=safe_relative(log_path) if log_path.exists() else None,
            compiler=compiler,
            errors=[f"LaTeX compilation timed out after {timeout_seconds} seconds."],
        )

    combined_output = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        errors.append(
            combined_output[-4000:]
            or "LaTeX compilation failed with no compiler output."
        )
    if "warning" in combined_output.lower():
        warnings.append(
            "Compiler output contains warnings. Review the .log file if formatting looks wrong."
        )
    docx_path = output_dir / f"{filename_base}.docx"
    docx_success = False
    try:
        from .docx import convert_tex_to_docx
        convert_tex_to_docx(tex_path, docx_path)
        docx_success = docx_path.exists()
    except Exception as e:
        warnings.append(f"DOCX export failed: {e}")

    success = (result.returncode == 0 and pdf_path.exists()) or docx_success
    if not success and not errors:
        errors.append("LaTeX compiler completed, but the expected PDF was not created.")

    return CompileResponse(
        success=success,
        filename_base=filename_base,
        tex_path=safe_relative(tex_path),
        pdf_path=safe_relative(pdf_path) if pdf_path.exists() else None,
        docx_path=safe_relative(docx_path) if docx_path.exists() else None,
        docx_download_url=f"/api/files/{filename_base}/{filename_base}.docx" if docx_path.exists() else None,
        log_path=safe_relative(log_path) if log_path.exists() else None,
        pdf_download_url=f"/api/files/{filename_base}/{filename_base}.pdf"
        if (result.returncode == 0 and pdf_path.exists())
        else None,
        compiler=compiler,
        errors=errors,
        warnings=warnings,
    )


def sanitize_date_folder(value: str) -> str:
    cleaned = re.sub(r"[^0-9\-]+", "", value.strip()).strip("-")
    return cleaned or datetime.now().strftime("%Y-%m-%d")


def compile_latex_to_docx(
    latex_code: str,
    candidate_name: str,
    company_name: str,
    role_name: str,
    date_str: str | None = None,
) -> CompileResponse:
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    date_folder = sanitize_date_folder(date_str)
    output_dir = GENERATED_ROOT / date_folder
    output_dir.mkdir(parents=True, exist_ok=True)

    filename_base = build_filename_base(candidate_name, company_name, role_name)
    docx_path = output_dir / f"{filename_base}.docx"
    tex_path = output_dir / f"{filename_base}.tex"

    errors: list[str] = []
    warnings: list[str] = []
    try:
        from .docx import convert_tex_to_docx
        convert_tex_to_docx(latex_code, docx_path)
    except Exception as e:
        errors.append(f"DOCX conversion failed: {e}")
    finally:
        # Guarantee no .tex files linger in the output directory
        if tex_path.exists():
            tex_path.unlink(missing_ok=True)

    success = docx_path.exists()
    return CompileResponse(
        success=success,
        filename_base=filename_base,
        tex_path=None,
        docx_path=safe_relative(docx_path) if success else None,
        docx_download_url=f"/api/files/{date_folder}/{filename_base}.docx" if success else None,
        errors=errors,
        warnings=warnings,
    )


def resolve_generated_file(*path_segments: str) -> Path | None:
    """Safely resolves a generated file by single string path (e.g. '2026-09-27/file.docx')
    or multiple segments (e.g. '2026-09-27', 'file.docx') within GENERATED_ROOT.
    Prevents path traversal attacks.
    """
    if not path_segments:
        return None

    parts: list[str] = []
    for seg in path_segments:
        if not seg:
            continue
        cleaned_seg = str(seg).replace("\\", "/")
        for p in cleaned_seg.split("/"):
            p_strip = p.strip()
            if p_strip and p_strip != ".":
                if p_strip == "..":
                    return None  # Path traversal attempt
                parts.append(p_strip)

    if not parts:
        return None

    candidate = GENERATED_ROOT.joinpath(*parts).resolve()
    try:
        candidate.relative_to(GENERATED_ROOT.resolve())
    except ValueError:
        return None

    if candidate.exists() and candidate.is_file():
        return candidate

    return None
