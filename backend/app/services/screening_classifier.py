import re
import json
import logging
from openai import OpenAI

from ..core.config import get_settings
from ..models.schemas import ScreenJobRequest, ScreenJobResponse

logger = logging.getLogger("uvicorn.error")

_INTERNSHIP_TITLE_RE = re.compile(r"\b(intern|interns|internship|internships|co-?op)\b", re.IGNORECASE)

_CLEARANCE_RE = re.compile(
    r"top secret|\bts/sci\b|\bsecret clearance\b|polygraph"
    r"|\b(active|current|valid|existing)\b[^.\n]{0,40}\bclearance\b"
    r"|\bclearance\b[^.\n]{0,20}\b(is\s+)?required\b"
    r"|\b(require[sd]?|must\s+(have|hold|possess|obtain|be\s+able\s+to\s+obtain)|ability\s+to\s+(obtain|maintain))\b[^.\n]{0,60}\bclearance\b"
    r"|\bpublic\s+trust\b"
    r"|\bdod\s+(secret|top\s+secret|clearance)\b"
    r"|\b(clearance|security)\s+eligibility\b"
    r"|\b(eligible\s+(to\s+obtain|for)|eligibility\s+for)\b[^.\n]{0,40}\bclearance\b"
    r"|\binterim\s+(secret|clearance)\b"
    r"|\bgovernment\s+security\s+(investigation|clearance)\b",
    re.IGNORECASE,
)

_CITIZENSHIP_RE = re.compile(
    r"\bmust\s+be\s+(a\s+)?u\.?\s?s\.?\s+citizens?\b"
    r"|\bu\.?\s?s\.?\s+citizenship\b[^.\n]{0,20}\b(is\s+)?required\b"
    r"|\bcitizenship\s+(is\s+)?required\b"
    r"|\bonly\s+u\.?\s?s\.?\s+citizens\b",
    re.IGNORECASE,
)

_EXPORT_CONTROL_RE = re.compile(
    r"\bitar\b|export control laws|export authorization|authorization to receive[^.\n]{0,60}controlled"
    r"|\bmust\s+be\s+a\s+u\.?\s?s\.?\s+persons?\b|\bu\.?\s?s\.?\s+person\s+status\b",
    re.IGNORECASE,
)

# Equal-opportunity boilerplate mentions citizenship without requiring it.
_EEO_SENTENCE_RE = re.compile(
    r"without regard to|regardless of|do(es)? not discriminate|equal (employment )?opportunity|protected (veteran|characteristic|status)",
    re.IGNORECASE,
)

_NO_SPONSORSHIP_RE = re.compile(
    r"\b(does\s+not|do\s+not|doesn't|don't|will\s+not|won't|cannot|can't|unable\s+to|not\s+able\s+to)\b[^.\n]{0,25}\bsponsor"
    r"|\bno\s+(visa\s+|h-?1b\s+|immigration\s+|work\s+visa\s+)?sponsorship\b"
    r"|\bwithout\b[^.\n]{0,40}\bsponsorship\b"
    r"|\bsponsorship\b[^.\n;,]{0,30}\bnot\s+(be\s+)?(available|offered|provided|considered)\b"
    r"|\bnot\s+(be\s+)?(eligible|considering|considered)\b[^.\n]{0,40}\bsponsorship\b"
    r"|\b(require|requires|need|needs)\b[^.\n]{0,40}\bsponsorship\b[^.\n]{0,60}\b(not\s+be\s+considered|ineligible|not\s+eligible)\b",
    re.IGNORECASE,
)

_GPU_TITLE_RE = re.compile(r"\b(gpu|cuda|hpc|high[- ]performance computing)\b", re.IGNORECASE)

# Hardware-level GPU terms; ordinary ML roles rarely use three or more of these.
_GPU_HARDWARE_TERMS = {
    "tensor cores": r"\btensor cores?\b",
    "memory bandwidth": r"\bmemory bandwidth\b",
    "cache behavior": r"\bcache (behavior|hierarchy|locality)\b",
    "cuda": r"\bcuda\b",
    "triton": r"\btriton\b",
    "nsight": r"\bnsight\b",
    "cutlass": r"\bcutlass\b",
    "ptx": r"\bptx\b",
    "kernel fusion": r"\bkernel (fusion|optimization|tuning)\b",
    "gpu interconnects": r"\b(nvlink|gpu interconnects?|infiniband)\b",
    "cpu-gpu data movement": r"\bdata movement between cpu and gpu\b|\bcpu[- /]gpu\b",
    "roofline": r"\broofline\b",
}

_NO_CLEARANCE_RE = re.compile(
    r"\bno\b[^.\n]{0,25}\bclearance\b|\bclearance\b[^.\n]{0,25}\bnot\s+(required|needed|necessary)\b",
    re.IGNORECASE,
)

# Python AND a systems language the candidate does not have (Go / C++ / Rust).
# Do not treat "Python, C++, or Go" menus as a match; those stay eligible via the OR rule.
_SYSTEMS_LANG_AND_RE = re.compile(
    r"\bpython\b.{0,120}\bplus\b.{0,100}(\bsystems languages?\b|\bgo\b|\bgolang\b|\bc\+\+\b|\brust\b)"
    r"|\bplus\b.{0,50}\bsystems languages?\b"
    r"|\bsystems languages?\b.{0,60}\(\s*(go|golang|c\+\+|rust)"
    r"|\bpython\b.{0,50}\bas well as\b.{0,50}\b(go\b|golang|c\+\+|rust)\b"
    r"|\b(go|golang|c\+\+|rust)\b.{0,50}\bas well as\b.{0,50}\bpython\b"
    r"|\bpython\b.{0,40}\band\b.{0,20}(at least one\s+)?(of\s+)?(go\b|golang|c\+\+|rust)\b",
    re.IGNORECASE,
)


def check_custom_guardrails(text: str) -> tuple[str, str] | None:
    """Checks custom golden guardrails from the database for exact phrase matches."""
    try:
        from .job_queue import get_screening_guardrails
        guardrails = get_screening_guardrails(limit=50)
        text_lower = text.lower()
        for g in guardrails:
            snippet = (g.get("overlooked_text") or "").strip().lower()
            if snippet and len(snippet) >= 6 and snippet in text_lower:
                reason = g.get("reason") or "Golden Guardrail"
                return reason, f"Matches user golden guardrail phrase: \"{g['overlooked_text']}\""
    except Exception:
        pass
    return None


def hard_disqualifier(title: str, job_description: str) -> tuple[str, str] | None:
    """Rule-based checks that run before the AI: internships, hard clearance/citizenship requirements,
    employers that don't sponsor visas, and user golden guardrails.
    Returns (flag_reason, explanation) or None.
    """
    custom_guardrail = check_custom_guardrails(f"{title}\n{job_description}" if title else (job_description or ""))
    if custom_guardrail:
        return custom_guardrail

    if _INTERNSHIP_TITLE_RE.search(title or ""):
        return "Internship", f"Title '{title}' is an internship/co-op role."

    if _GPU_TITLE_RE.search(title or ""):
        return "GPU/HPC Performance", f"Title '{title}' is a GPU/HPC specialization."
    gpu_terms = [name for name, pattern in _GPU_HARDWARE_TERMS.items()
                 if re.search(pattern, job_description or "", re.IGNORECASE)]
    if len(gpu_terms) >= 3:
        return "GPU/HPC Performance", f"GPU hardware-level work: {', '.join(gpu_terms)}."

    systems_match = _SYSTEMS_LANG_AND_RE.search(job_description or "")
    if systems_match:
        snippet = systems_match.group(0).strip()[:200]
        return "Systems Language", f"Requires Python plus Go/C++/Rust: \"{snippet}\""

    # Don't split after single-letter abbreviations like "U.S."
    sentences = re.split(r"(?<=[.!?])(?<![A-Z]\.)\s+|\n+", job_description or "")
    for sentence in sentences:
        if not sentence.strip():
            continue
        snippet = sentence.strip()[:200]
        if _CLEARANCE_RE.search(sentence) and not _NO_CLEARANCE_RE.search(sentence):
            return "Security Clearance", f"Requires security clearance: \"{snippet}\""
        # Only citizenship needs the EEO guard; export-control clauses often say "protected status" too.
        if _CITIZENSHIP_RE.search(sentence) and not _EEO_SENTENCE_RE.search(sentence):
            return "Citizenship Required", f"Requires U.S. citizenship: \"{snippet}\""
        if _EXPORT_CONTROL_RE.search(sentence):
            return "Export Control", f"Export-controlled role (ITAR/EAR): \"{snippet}\""
        if _NO_SPONSORSHIP_RE.search(sentence):
            return "No Sponsorship", f"Does not sponsor work visas: \"{snippet}\""
    return None


_JAVA_TOKEN_RE = re.compile(r"\bjava\b(?!script)|\bspring\s*boot\b", re.IGNORECASE)
_DOTNET_TOKEN_RE = re.compile(r"\b\.net\b|\basp\.net\b|\bc#\b|\bcsharp\b", re.IGNORECASE)
_PYTHON_TOKEN_RE = re.compile(r"\bpython\b|\bfastapi\b|\bdjango\b", re.IGNORECASE)
_NODE_TOKEN_RE = re.compile(
    r"\btypescript\b|\bnode\.?js\b|\breact\b|\bnestjs\b|\bjavascript\b",
    re.IGNORECASE,
)
_AI_TOKEN_RE = re.compile(
    r"\brag\b|\bllm\b|\blangchain\b|\blanggraph\b|\bvector (search|database|db)\b|\bprompt (design|engineering)\b",
    re.IGNORECASE,
)
_DEST_NODE_RE = re.compile(
    r"into (a |an )?(clean )?(typescript|node\.?js)"
    r"|typescript\s*/\s*node"
    r"|node\.?js\s*/\s*typescript"
    r"|strong typescript"
    r"|typescript skills",
    re.IGNORECASE,
)


def infer_primary_stack(title: str, job_description: str, technical_tools: list[str] | None = None) -> str:
    """Picks the job's destination stack. JavaScript is not Java. Leftover C#/Python being
    migrated onto TypeScript/Node does not make the job a .NET or Python role.
    """
    hay = f"{title or ''}\n{job_description or ''}\n{' '.join(technical_tools or [])}"
    if _DEST_NODE_RE.search(hay):
        return "node"

    has_java = bool(
        re.search(r"\bjava\b(?!script)", hay, re.IGNORECASE)
        or re.search(r"\bspring\s*boot\b", hay, re.IGNORECASE)
    )
    has_ts_node = bool(re.search(r"\btypescript\b|\bnode\.?js\b|\bnestjs\b", hay, re.IGNORECASE))
    has_react = bool(re.search(r"\breact\b", hay, re.IGNORECASE))
    has_dotnet = bool(_DOTNET_TOKEN_RE.search(hay))
    has_python = bool(_PYTHON_TOKEN_RE.search(hay))
    has_ai = bool(_AI_TOKEN_RE.search(hay))

    if has_java:
        return "java"
    if has_ts_node:
        return "node"
    if has_dotnet and not has_python:
        return "dotnet"
    if has_ai and not has_python:
        return "ai"
    if has_python:
        return "python"
    if has_dotnet:
        return "dotnet"
    if has_react:
        return "node"
    if has_ai:
        return "ai"
    return "ai"


def clean_json_text(text: str) -> str:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        return m.group(0).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
    return text


def screen_job_with_ai(request: ScreenJobRequest) -> ScreenJobResponse:
    """
    Evaluates a job description against candidate capabilities (Java/Spring Boot, Python/FastAPI/AI, C#/.NET, Full-Stack)
    exclusively via OpenAI / OpenRouter client.
    """
    settings = get_settings()

    system_instruction = (
        "You are an expert technical recruiting classifier. Evaluate whether the job description matches the candidate's core profile.\n\n"
        "CANDIDATE PROFILE:\n"
        "- Role: Full-Stack / Backend / Software Engineer / AI Engineer (0-3 years experience)\n"
        "- Core Stack: Java (Spring Boot, Microservices, Kafka), Python (FastAPI, Django, AI/ML/LLMs), C# (.NET, Entity Framework), TypeScript/JavaScript (React, Node.js), SQL, Cloud (Docker, Kubernetes, AWS/Azure).\n"
        "- The candidate does not specialize in pure/exclusive C++ low-level systems, pure hardware board bring-up/ASIC, or active military security clearances.\n\n"
        "ELIGIBILITY RULES & STACK DETECTION:\n"
        "1. ELIGIBLE (eligible: true, flag_reason: null):\n"
        "   - Roles focused on Backend, Full-Stack, Web, Cloud, AI/ML, or general Software Engineering.\n"
        "   - MULTI-LANGUAGE MENUS / 'ONE OR MORE OF': If the job description lists multiple languages or options (e.g. 'One or more of C++, C#, Java, Python, .NET', 'Proficiency in Java, Python, or C++', 'C, C++, C#, Java, Python'), and at least ONE of the candidate's core languages (Java, Python, C#/.NET, TypeScript/JavaScript) is listed or accepted, mark ELIGIBLE (true).\n"
        "   - AND vs OR: 'Python or C++' / 'one of Python, Go, C++' is OR and can be ELIGIBLE. 'Python PLUS Go/C++/Rust', 'Python and C++', or 'Python plus a systems language' is AND. The candidate does not have Go, C++, or Rust, so those AND requirements are INELIGIBLE.\n"
        "   - DETECT PRIMARY STACK: Choose the stack the JOB requires you to write in ('java', 'python', 'dotnet', 'node', 'ai'). This is the destination stack, not whichever language happens to appear in the candidate profile. 'Strong TypeScript' / 'TypeScript/Node.js stack' / 'refactor into TypeScript' is 'node' even if leftover C#, Python, or VB is being replaced. JavaScript is not Java. LLM/RAG work on a TypeScript/Node role is still 'node'. Only use 'ai' when the role is primarily an ML/LLM job without a TypeScript/Java/C#/Python product-stack mandate.\n"
        "   - Boilerplate company language lists (e.g. Walmart, Disney, Garmin, L3Harris, Lockheed) where Java, Python, C#, or web technologies are supported are ALWAYS ELIGIBLE (true).\n"
        "   - Standard Equal Opportunity (EEO) non-discrimination notices are ELIGIBLE (true).\n"
        "   - Mentions of 'embedded' in a cloud, analytics, migration, or broad multi-option context are ELIGIBLE (true).\n\n"
        "2. INELIGIBLE / FLAGGED (eligible: false, flag_reason must be one of: 'Exclusive C/C++', 'Systems Language', 'Security Clearance', 'Embedded/Firmware', 'Hardware/FPGA', 'CUDA'):\n"
        "   - 'Exclusive C/C++': C or C++ is STRICTLY and EXCLUSIVELY mandatory with NO high-level language alternative (e.g. pure C++ 5G PHY stack, pure Unreal engine C++ core, kernel driver development).\n"
        "   - 'Systems Language': The role requires Python (or another high-level language) AND a systems language the candidate does not have: Go, C++, or Rust. Example: 'Strong proficiency in Python plus at least one systems language (Go, C++, or Rust)'.\n"
        "   - 'Security Clearance': Explicit requirement that the applicant currently holds an ACTIVE DoD Secret / Top Secret clearance.\n"
        "   - 'Embedded/Firmware': Pure low-level microcontroller register programming, board bring-up, or device driver development where high-level languages (Java, C#, Python) are NOT applicable.\n"
        "   - 'Hardware/FPGA': Pure hardware circuit design, VHDL, Verilog, ASIC synthesis.\n"
        "   - 'CUDA': Low-level GPU kernel shader/CUDA/Triton programming, OR roles whose core responsibility is GPU / HPC performance engineering "
        "(profiling GPU hardware behavior, memory bandwidth, cache behavior, tensor cores, CPU-GPU data movement, kernel-level optimization of model workloads). "
        "Flag these even when Python or PyTorch is also required, because the multi-language rule does not apply to GPU performance specialization. "
        "AI/ML or backend roles that merely train, fine-tune, or serve models on GPUs stay ELIGIBLE.\n\n"
        "Return ONLY a JSON object with this structure (no markdown fences):\n"
        "{\n"
        '  "eligible": true,\n'
        '  "flag_reason": null,\n'
        '  "primary_stack": "java" | "python" | "dotnet" | "node" | "ai" | "cpp" | "hardware" | "other",\n'
        '  "confidence": 0.95,\n'
        '  "explanation": "Short 1-2 sentence explanation of why this job matches the candidate stack or why it is disqualified."\n'
        "}"
    )

    try:
        from .job_queue import get_screening_guardrails
        recent_guardrails = get_screening_guardrails(limit=8)
        if recent_guardrails:
            guardrail_examples = []
            for g in recent_guardrails:
                r = g.get("reason", "Ineligible")
                snip = g.get("overlooked_text") or "Flagged by candidate as disqualifying"
                t = g.get("job_title") or "Role"
                c = g.get("company") or "Company"
                guardrail_examples.append(f"- [{r}] ({t} @ {c}): \"{snip}\"")
            system_instruction += (
                "\n\nHUMAN CORRECTIONS & GOLDEN GUARDRAILS (Do not overlook these disqualifiers):\n"
                + "\n".join(guardrail_examples)
                + "\nAlways flag jobs that match or resemble these user-verified disqualifiers.\n"
            )
    except Exception:
        pass

    tools_str = ", ".join(request.technical_tools) if request.technical_tools else "None"
    prompt = (
        f"Job Title: {request.title or 'Unknown'}\n"
        f"Company: {request.company or 'Unknown'}\n"
        f"Location: {request.location or 'Unknown'}\n"
        f"Technical Tools Tagged: {tools_str}\n\n"
        f"Job Description:\n{request.job_description[:6000]}"
    )

    import time
    t0 = time.time()
    msg_start = f"[Screening Classifier] Evaluating: {request.title} @ {request.company} using model={settings.openai_model}"
    print(msg_start, flush=True)
    logger.info(msg_start)

    try:
        if settings.openai_api_key:
            client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=30.0,
            )
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ]
            completion = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.1,
                max_tokens=2048,
            )
            elapsed = round(time.time() - t0, 2)
            raw_text = clean_json_text(completion.choices[0].message.content or "")
            data = json.loads(raw_text)
            inferred = infer_primary_stack(
                request.title or "",
                request.job_description or "",
                request.technical_tools,
            )
            llm_stack = (data.get("primary_stack") or inferred or "ai").lower().strip()
            if data.get("eligible", True) and inferred == "node" and llm_stack != "node":
                stack = "node"
            elif data.get("eligible", True) and llm_stack == "java" and inferred != "java":
                stack = inferred
            else:
                stack = llm_stack
            msg_done = f"[Screening Classifier] OpenRouter responded in {elapsed}s: eligible={data.get('eligible')}, stack={stack} (llm={llm_stack}, inferred={inferred})"
            print(msg_done, flush=True)
            logger.info(msg_done)
            return ScreenJobResponse(
                eligible=bool(data.get("eligible", True)),
                flag_reason=data.get("flag_reason") if not data.get("eligible") else None,
                primary_stack=stack if data.get("eligible", True) else data.get("primary_stack"),
                confidence=float(data.get("confidence", 0.9)),
                explanation=data.get("explanation", "Evaluated by OpenAI screening classifier."),
            )

    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        msg_err = f"[Screening Classifier] OpenRouter call failed after {elapsed}s: {e}. Falling back to heuristic screening."
        print(msg_err, flush=True)
        logger.warning(msg_err)

    # Fallback heuristic if OpenAI unavailable
    jd_lower = request.job_description.lower()
    if "active security clearance" in jd_lower or "top secret" in jd_lower:
        return ScreenJobResponse(
            eligible=False,
            flag_reason="Security Clearance",
            primary_stack="other",
            confidence=0.7,
            explanation="Requires active security clearance (fallback rule).",
        )

    if ("rtos" in jd_lower or "microcontroller" in jd_lower) and not (
        re.search(r"\bjava\b(?!script)", jd_lower) or ".net" in jd_lower or "c#" in jd_lower
    ):
        return ScreenJobResponse(
            eligible=False,
            flag_reason="Embedded/Firmware",
            primary_stack="hardware",
            confidence=0.7,
            explanation="Requires low-level embedded RTOS/microcontroller (fallback rule).",
        )

    primary = infer_primary_stack(
        request.title or "",
        request.job_description or "",
        request.technical_tools,
    )
    return ScreenJobResponse(
        eligible=True,
        flag_reason=None,
        primary_stack=primary,
        confidence=0.75,
        explanation=f"Matches destination stack ({primary}) via fallback evaluator.",
    )
