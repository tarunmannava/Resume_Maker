import re
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel

class CompileResponse(BaseModel):
    success: bool
    filename_base: str
    tex_path: str
    pdf_path: str | None = None
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


def sanitize_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "Resume"
    if cleaned.upper() in WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned}_Resume"
    return cleaned[:80]


def build_filename_base(candidate_name: str, company_name: str, role_name: str) -> str:
    parts = [
        sanitize_filename_part(candidate_name),
        sanitize_filename_part(company_name),
        sanitize_filename_part(role_name),
    ]
    return "_".join(parts)


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
        if compiler_available("latexmk"):
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

    success = result.returncode == 0 and pdf_path.exists()
    if not success and not errors:
        errors.append("LaTeX compiler completed, but the expected PDF was not created.")

    return CompileResponse(
        success=success,
        filename_base=filename_base,
        tex_path=safe_relative(tex_path),
        pdf_path=safe_relative(pdf_path) if pdf_path.exists() else None,
        log_path=safe_relative(log_path) if log_path.exists() else None,
        pdf_download_url=f"/api/files/{filename_base}/{filename_base}.pdf"
        if success
        else None,
        compiler=compiler,
        errors=errors,
        warnings=warnings,
    )


def resolve_generated_file(folder: str, filename: str) -> Path | None:
    safe_folder = sanitize_filename_part(folder)
    safe_filename = (
        sanitize_filename_part(Path(filename).stem) + Path(filename).suffix.lower()
    )
    candidate = (GENERATED_ROOT / safe_folder / safe_filename).resolve()
    try:
        candidate.relative_to(GENERATED_ROOT.resolve())
    except ValueError:
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate
