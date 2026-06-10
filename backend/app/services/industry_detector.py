"""Industry detection from job descriptions with weighted signals and false-positive guards."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Must match frontend industry dropdown (+ extras used in rewrite prompts)
CANONICAL_INDUSTRIES = (
    "Fintech",
    "Healthcare",
    "E-commerce",
    "Cybersecurity",
    "SaaS",
    "Edtech",
    "Media",
    "Supply Chain",
    "Automotive",
    "Government",
    "General Technology",
)

INDUSTRY_ALIASES: dict[str, str] = {
    "finance": "Fintech",
    "financial services": "Fintech",
    "banking": "Fintech",
    "payments": "Fintech",
    "health": "Healthcare",
    "health care": "Healthcare",
    "medtech": "Healthcare",
    "biotech": "Healthcare",
    "life sciences": "Healthcare",
    "retail": "E-commerce",
    "ecommerce": "E-commerce",
    "e commerce": "E-commerce",
    "security": "Cybersecurity",
    "infosec": "Cybersecurity",
    "cyber security": "Cybersecurity",
    "saas": "SaaS",
    "b2b saas": "SaaS",
    "software as a service": "SaaS",
    "education": "Edtech",
    "ed tech": "Edtech",
    "edtech": "Edtech",
    "entertainment": "Media",
    "streaming": "Media",
    "logistics": "Supply Chain",
    "supply chain": "Supply Chain",
    "automotive": "Automotive",
    "auto": "Automotive",
    "ev": "Automotive",
    "public sector": "Government",
    "federal": "Government",
    "tech": "General Technology",
    "technology": "General Technology",
    "software": "General Technology",
}

# Known employers / brands → industry (checked on company_context + JD)
COMPANY_INDUSTRY_HINTS: list[tuple[str, str, int]] = [
    (r"\b(stripe|paypal|square|robinhood|coinbase|plaid|affirm|visa|mastercard|capital one|jpmorgan|chase|goldman|morgan stanley|bloomberg)\b", "Fintech", 8),
    (r"\b(epic systems|unitedhealth|anthem|cigna|kaiser|pfizer|moderna|johnson & johnson|medtronic|mayo clinic|shands)\b", "Healthcare", 8),
    (r"\b(amazon(?! web services)|walmart|target|shopify|ebay|etsy|instacart|doordash)\b", "E-commerce", 8),
    (r"\b(crowdstrike|palo alto networks|okta|zscaler|fortinet|mandiant|splunk security)\b", "Cybersecurity", 8),
    (r"\b(salesforce|servicenow|workday|hubspot|zendesk|atlassian|snowflake(?! data))\b", "SaaS", 6),
    (r"\b(coursera|duolingo|chegg|blackboard|instructure)\b", "Edtech", 8),
    (r"\b(netflix|spotify|disney\+?|hulu|tiktok|meta(?!data))\b", "Media", 6),
    (r"\b(fedex|ups|dhl|maersk|flexport)\b", "Supply Chain", 8),
    (r"\b(tesla|rivian|lucid|ford motor|general motors|waymo)\b", "Automotive", 8),
    (r"\b(nasa|department of defense|dod\b|usps|irs)\b", "Government", 7),
]

# Global phrases that suppress false positives (subtract from all or specific industries)
GLOBAL_NEGATIVE_PATTERNS: list[str] = [
    r"\bhealth checks?\b",
    r"\bapplication health\b",
    r"\bservice health\b",
    r"\bendpoint health\b",
]

INDUSTRY_NEGATIVE: dict[str, list[str]] = {
    "Healthcare": [
        r"\bhealth checks?\b",
        r"\bmental health of (the )?system\b",
    ],
    "Cybersecurity": [
        r"\bspring security\b",
        r"\boauth\b",
        r"\bjwt\b",
        r"\buser authentication\b",
        r"\brole[- ]based access\b",
        r"\bapi security\b",  # often app dev, not cyber company
    ],
    "Edtech": [
        r"\bmachine learning\b",
        r"\bdeep learning\b",
        r"\breinforcement learning\b",
        r"\btransfer learning\b",
        r"\bonline learning rate\b",
    ],
    "Fintech": [
        r"\btransaction logs?\b",  # generic DB
    ],
    "SaaS": [
        r"\benterprise architect\b",  # alone too weak
    ],
}

# (pattern, weight) — higher weight = stronger signal
INDUSTRY_STRONG: dict[str, list[tuple[str, int]]] = {
    "Fintech": [
        (r"\bfintech\b", 6),
        (r"\bbanking (platform|system|api)\b", 6),
        (r"\bpayment processing\b", 6),
        (r"\bcredit (card|lending)\b", 5),
        (r"\bloan origination\b", 5),
        (r"\btrading platform\b", 5),
        (r"\bcapital markets\b", 5),
        (r"\bunderwriting\b", 4),
        (r"\bkyc\b", 4),
        (r"\baml\b", 4),
        (r"\banti[- ]money laundering\b", 5),
        (r"\bwire transfer\b", 4),
        (r"\bneobank\b", 5),
        (r"\binsurance (claims|policy)\b", 4),
    ],
    "Healthcare": [
        (r"\bhipaa\b", 8),
        (r"\behr\b", 6),
        (r"\belectronic health record\b", 7),
        (r"\bclinical (trial|workflow|data)\b", 7),
        (r"\bpatient (data|records|portal)\b", 7),
        (r"\bmedical (records?|device|imaging)\b", 6),
        (r"\bhealthcare (platform|system|provider)\b", 7),
        (r"\bhospital (system|network)\b", 6),
        (r"\bpharma(ceutical)?\b", 5),
        (r"\bdiagnos(is|tic)\b", 4),
        (r"\bprior authorization\b", 6),
        (r"\bhipaa[- ]compliant\b", 8),
    ],
    "E-commerce": [
        (r"\be[- ]?commerce\b", 7),
        (r"\bonline (retail|store|marketplace)\b", 6),
        (r"\bshopping cart\b", 6),
        (r"\bcheckout (flow|experience)\b", 6),
        (r"\bproduct catalog\b", 5),
        (r"\border fulfillment\b", 6),
        (r"\binventory management\b", 4),
        (r"\bmerchant (platform|services)\b", 5),
        (r"\bconversion (rate|funnel)\b", 4),
    ],
    "Cybersecurity": [
        (r"\bcybersecurity\b", 8),
        (r"\bcyber security\b", 8),
        (r"\binformation security\b", 7),
        (r"\bsecurity operations\b", 7),
        (r"\bsoc (analyst|engineer)\b", 7),
        (r"\bthreat (detection|hunting|intelligence)\b", 7),
        (r"\bvulnerability (management|assessment)\b", 7),
        (r"\bpenetration test(ing)?\b", 7),
        (r"\bsiem\b", 6),
        (r"\bincident response\b", 6),
        (r"\bzero trust\b", 6),
        (r"\bmalware\b", 6),
        (r"\bransomware\b", 6),
    ],
    "SaaS": [
        (r"\bsaas\b", 8),
        (r"\bsoftware as a service\b", 8),
        (r"\bmulti[- ]tenant (saas|platform|architecture)\b", 7),
        (r"\bb2b saas\b", 7),
        (r"\bsubscription (billing|revenue)\b", 5),
        (r"\bproduct[- ]led growth\b", 4),
    ],
    "Edtech": [
        (r"\bedtech\b", 8),
        (r"\bed[- ]?tech\b", 8),
        (r"\blms\b", 6),
        (r"\blearning management system\b", 7),
        (r"\bcurriculum (design|platform)\b", 6),
        (r"\bstudent information system\b", 7),
        (r"\bclassroom (platform|software)\b", 6),
        (r"\bk[- ]?12\b", 5),
        (r"\bhigher education (platform|software)\b", 6),
    ],
    "Media": [
        (r"\bstreaming (platform|service)\b", 6),
        (r"\bvideo (platform|streaming)\b", 5),
        (r"\bcontent delivery (network|platform)\b", 5),
        (r"\badtech\b", 5),
        (r"\bdigital publishing\b", 5),
        (r"\bgame (studio|development|platform)\b", 5),
        (r"\bsocial media platform\b", 5),
    ],
    "Supply Chain": [
        (r"\bsupply chain\b", 7),
        (r"\blogistics (platform|system)\b", 6),
        (r"\bwarehouse management\b", 6),
        (r"\bfleet management\b", 5),
        (r"\blast[- ]mile delivery\b", 6),
        (r"\bprocurement (platform|system)\b", 5),
        (r"\bdistribution center\b", 5),
    ],
    "Automotive": [
        (r"\bautonomous (driving|vehicle)\b", 7),
        (r"\belectric vehicle\b", 6),
        (r"\bautomotive (software|industry)\b", 7),
        (r"\bvehicle telemetry\b", 6),
        (r"\bover[- ]the[- ]air updates?\b", 5),
        (r"\bself[- ]driving\b", 7),
        (r"\bpowertrain\b", 6),
        (r"\bin[- ]vehicle\b", 5),
    ],
    "Government": [
        (r"\bfederal (agency|government)\b", 7),
        (r"\bpublic sector\b", 6),
        (r"\bclearance (required|eligible)\b", 5),
        (r"\bstate (agency|government)\b", 5),
        (r"\bcivic tech\b", 5),
    ],
}

INDUSTRY_WEAK: dict[str, list[tuple[str, int]]] = {
    "Fintech": [
        (r"\bbank(ing)?\b", 2),
        (r"\bpayments?\b", 2),
        (r"\bfraud (detection|prevention)\b", 3),
        (r"\bledger\b", 2),
    ],
    "Healthcare": [
        (r"\bhealthcare\b", 3),
        (r"\bmedical\b", 2),
        (r"\bclinical\b", 2),
    ],
    "E-commerce": [
        (r"\bretail\b", 2),
        (r"\bmarketplace\b", 2),
    ],
    "Cybersecurity": [
        (r"\bcryptography\b", 3),
        (r"\bencryption at rest\b", 3),
    ],
    "SaaS": [
        (r"\benterprise (saas|software)\b", 3),
        (r"\bworkflow (automation|platform)\b", 2),
    ],
    "Edtech": [
        (r"\beducation (technology|software)\b", 3),
        (r"\buniversity\b", 1),
    ],
    "Media": [
        (r"\bstreaming\b", 2),
        (r"\bgaming\b", 2),
    ],
    "Supply Chain": [
        (r"\bshipping\b", 2),
        (r"\binventory\b", 2),
    ],
}

MIN_INDUSTRY_SCORE = 4.0
MIN_MARGIN_RATIO = 1.35  # winner must beat runner-up by this factor when runner-up > 0


@dataclass
class IndustryDetectionResult:
    industry: str | None
    confidence: float  # 0.0 - 1.0
    scores: dict[str, float]


def _count_patterns(text: str, patterns: list[tuple[str, int]]) -> float:
    total = 0.0
    for pattern, weight in patterns:
        total += len(re.findall(pattern, text, re.IGNORECASE)) * weight
    return total


def _count_negative(text: str, patterns: list[str]) -> float:
    total = 0.0
    for pattern in patterns:
        total += len(re.findall(pattern, text, re.IGNORECASE)) * 2.5
    return total


def normalize_industry(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    cleaned = str(raw).strip()
    if cleaned in CANONICAL_INDUSTRIES:
        return cleaned
    lower = cleaned.lower()
    if lower in INDUSTRY_ALIASES:
        return INDUSTRY_ALIASES[lower]
    for alias, canonical in INDUSTRY_ALIASES.items():
        if alias in lower or lower in alias:
            return canonical
    for canonical in CANONICAL_INDUSTRIES:
        if canonical.lower() in lower:
            return canonical
    return None


def detect_industry_from_text(
    job_description: str,
    company_context: str | None = None,
) -> IndustryDetectionResult:
    """Score industries from JD + company context; return best match with confidence."""
    jd = job_description or ""
    ctx = company_context or ""
    combined = f"{jd}\n{ctx}".lower()

    scores: dict[str, float] = {name: 0.0 for name in CANONICAL_INDUSTRIES if name != "General Technology"}

    global_penalty = _count_negative(combined, GLOBAL_NEGATIVE_PATTERNS)

    for industry in scores:
        scores[industry] += _count_patterns(combined, INDUSTRY_STRONG.get(industry, []))
        scores[industry] += _count_patterns(combined, INDUSTRY_WEAK.get(industry, []))
        scores[industry] -= _count_negative(combined, INDUSTRY_NEGATIVE.get(industry, []))
        scores[industry] -= global_penalty * 0.25

    for pattern, industry, boost in COMPANY_INDUSTRY_HINTS:
        if re.search(pattern, combined, re.IGNORECASE):
            scores[industry] = scores.get(industry, 0) + boost

    # Drop non-positive
    positive = {k: v for k, v in scores.items() if v > 0}
    if not positive:
        return IndustryDetectionResult(industry=None, confidence=0.0, scores=scores)

    ranked = sorted(positive.items(), key=lambda x: x[1], reverse=True)
    winner, top_score = ranked[0]
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0

    if top_score < MIN_INDUSTRY_SCORE:
        return IndustryDetectionResult(industry=None, confidence=0.0, scores=scores)

    if runner_up_score > 0 and top_score < runner_up_score * MIN_MARGIN_RATIO:
        # Ambiguous between top two — low confidence
        confidence = min(0.45, top_score / (top_score + runner_up_score + 1))
        return IndustryDetectionResult(industry=winner, confidence=confidence, scores=scores)

    # Confidence scales with score strength and margin
    margin_bonus = 0.15 if runner_up_score == 0 or top_score >= runner_up_score * 2 else 0.0
    confidence = min(0.98, 0.35 + (top_score / 20.0) + margin_bonus)
    return IndustryDetectionResult(industry=winner, confidence=confidence, scores=scores)
