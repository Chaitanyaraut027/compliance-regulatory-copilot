"""
Compliance assessment — RAG-powered comparison of company evidence
against retrieved FSSAI regulatory requirements.
"""

from __future__ import annotations

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import json
import logging
from typing import Optional

import openai

from app.config import get_settings
from app.retriever import retrieve
from app.schemas import (
    ComplianceRequest,
    ComplianceResponse,
    ComplianceFinding,
    RegulatorySource,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a food regulatory compliance analyst.  Your task is to compare company-supplied evidence against FSSAI regulatory requirements that have been retrieved from official documents.

CRITICAL RULES:
1. Base your analysis ONLY on the regulatory excerpts provided below.  Do NOT invent clauses, limits, citations, or page numbers.
2. If the retrieved excerpts are insufficient to assess a requirement, return status "NEEDS_REVIEW" and explain the limitation.
3. Distinguish clearly between:
   - COMPLIANT: sufficient evidence supports the requirement
   - PARTIALLY_COMPLIANT: some evidence exists but required elements are missing
   - NEEDS_ATTENTION: mandatory regulatory requirements, labelling declarations, or required evidence are missing
   - MISSING_EVIDENCE: no adequate supporting company evidence was found (this is NOT the same as non-compliance)
   - POTENTIALLY_NON_COMPLIANT: evidence directly contradicts or violates a requirement
   - NEEDS_REVIEW: evidence is ambiguous, conflicting, outdated, or insufficient
4. Absence of evidence does NOT automatically establish a regulatory violation.
5. Distinguish regulatory requirements from your own recommendations.
6. This is NOT an official legal determination or certification.

Return your analysis as a JSON object with this structure:
{
  "overall_status": "<one of the five statuses>",
  "summary": "<brief overall summary>",
  "findings": [
    {
      "requirement": "<specific regulatory requirement>",
      "status": "<status>",
      "explanation": "<detailed explanation>",
      "evidence_found": ["<list of evidence items found>"],
      "evidence_missing": ["<list of missing evidence items>"],
      "recommended_actions": ["<actionable next steps>"]
    }
  ]
}

Return ONLY the JSON object.  No markdown fences, no preamble.
"""


def _build_context(retrieved_chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    parts = []
    for i, ch in enumerate(retrieved_chunks, 1):
        source = (
            f"[Source {i}] {ch.get('doc_title', ch.get('doc_filename', 'Unknown'))} "
            f"| Pages {ch.get('page_start', '?')}–{ch.get('page_end', '?')}"
        )
        section = ch.get("section_title")
        if section:
            source += f" | Section: {section}"
        sim = ch.get("similarity")
        if sim is not None:
            source += f" | Similarity: {sim:.3f}"
        parts.append(f"{source}\n{ch['content']}")
    return "\n\n---\n\n".join(parts)


def _build_sources(retrieved_chunks: list[dict]) -> list[RegulatorySource]:
    sources = []
    for ch in retrieved_chunks:
        sources.append(RegulatorySource(
            document_name=ch.get("doc_title") or ch.get("doc_filename", "Unknown"),
            page_start=ch.get("page_start"),
            page_end=ch.get("page_end"),
            section=ch.get("section_title"),
            excerpt=ch["content"][:300],
            similarity=ch.get("similarity"),
        ))
    return sources


def assess_compliance(request: ComplianceRequest) -> ComplianceResponse:
    """
    End-to-end compliance assessment:
    1. Retrieve relevant regulatory chunks.
    2. Ask the LLM to compare evidence vs requirements.
    3. Return structured findings.
    """
    settings = get_settings()

    # ── Step 1: Retrieve ──
    retrieved = retrieve(
        query=request.question,
        top_k=request.top_k,
    )

    sources = _build_sources(retrieved)

    if not retrieved:
        return ComplianceResponse(
            question=request.question,
            overall_status="NEEDS_REVIEW",
            summary=(
                "No relevant regulatory content was retrieved from the database. "
                "This may mean the regulatory PDFs have not been ingested, or the "
                "query does not match any indexed content."
            ),
            findings=[],
            retrieved_sources=sources,
        )

    # ── Step 2: Build prompt ──
    context = _build_context(retrieved)

    user_message = f"""\
## Compliance Question
{request.question}

## Company Evidence
{request.company_evidence}
"""
    if request.facility_description:
        user_message += f"\n## Facility Description\n{request.facility_description}\n"
    if request.compliance_area:
        user_message += f"\n## Compliance Area\n{request.compliance_area}\n"

    user_message += f"""
## Retrieved Regulatory Excerpts
{context}

Analyze the company evidence against the retrieved regulatory requirements.
Return the JSON analysis.
"""

    # ── Step 3: Call LLM (Groq [FREE] or OpenAI) ──
    provider = settings.llm_provider.lower()
    if provider == "groq" or (not settings.openai_api_key and settings.groq_api_key):
        if not settings.groq_api_key:
            return ComplianceResponse(
                question=request.question,
                overall_status="NEEDS_REVIEW",
                summary=(
                    "GROQ_API_KEY is not configured in .env. "
                    "You can get a 100% FREE API key from https://console.groq.com "
                    "and paste it into your .env file."
                ),
                findings=[],
                retrieved_sources=sources,
            )
        import groq
        client = groq.Groq(api_key=settings.groq_api_key)
        model = settings.groq_chat_model
    else:
        if not settings.openai_api_key:
            return ComplianceResponse(
                question=request.question,
                overall_status="NEEDS_REVIEW",
                summary="Neither GROQ_API_KEY nor OPENAI_API_KEY is configured in .env.",
                findings=[],
                retrieved_sources=sources,
            )
        import openai
        client = openai.OpenAI(api_key=settings.openai_api_key)
        model = settings.openai_chat_model

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        raw = completion.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return ComplianceResponse(
            question=request.question,
            overall_status="NEEDS_REVIEW",
            summary=f"LLM analysis failed ({model}): {exc}",
            findings=[],
            retrieved_sources=sources,
        )

    # ── Step 4: Parse response ──
    try:
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[:-3]
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM JSON: %s", raw[:500])
        return ComplianceResponse(
            question=request.question,
            overall_status="NEEDS_REVIEW",
            summary="The LLM returned a non-JSON response. Manual review is required.",
            findings=[],
            retrieved_sources=sources,
        )

    # ── Step 5: Build structured response ──
    findings = []
    for f in data.get("findings", []):
        # Attach regulatory source references to each finding
        finding_sources = []
        for s in sources:
            finding_sources.append(s)

        findings.append(ComplianceFinding(
            requirement=f.get("requirement", ""),
            status=f.get("status", "NEEDS_REVIEW"),
            explanation=f.get("explanation", ""),
            evidence_found=f.get("evidence_found", []),
            evidence_missing=f.get("evidence_missing", []),
            recommended_actions=f.get("recommended_actions", []),
            regulatory_sources=finding_sources,
        ))

    return ComplianceResponse(
        question=request.question,
        overall_status=data.get("overall_status", "NEEDS_REVIEW"),
        summary=data.get("summary", ""),
        findings=findings,
        retrieved_sources=sources,
    )
