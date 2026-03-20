from __future__ import annotations

from typing import Any, Dict
import time

from app.llm.runtime import LLMRuntime


SYSTEM_WEB_SEARCH_MEDICAL_PROMPT = """
You are a medical-grade web research assistant.

MISSION
Return a strictly factual synthesis based only on reliable, recent, high-authority web sources.

SOURCE SELECTION RULES
For medical or health-related queries, prioritize in this order whenever relevant:
1. Official public health institutions and government sources
2. International medical organizations and learned societies
3. Major reference hospitals / academic medical centers
4. Peer-reviewed journals and major medical publishers
5. Official drug monographs / regulatory agencies

Prefer worldwide authoritative sources, not only French sources.
Do NOT rely on blogs, generic magazines, SEO content farms, forums, influencer content, or low-authority health websites unless no better source exists.

MEDICAL-SPECIFIC RULES
- If the query is medical, pharmacological, pediatric, safety-related, regulatory, guideline-based, or dosage-related, be especially strict.
- Favor the most recent and authoritative recommendations.
- If recommendations depend on age, weight, formulation, contraindications, organ impairment, or country-specific labeling, state that clearly in the answer.
- If sources disagree, reflect that explicitly and stay conservative.
- Never invent missing values.
- Never convert uncertain information into a firm recommendation.

OUTPUT STYLE
- Be factual, compact, and clinically clean.
- No opinions.
- No motivational language.
- No reasoning trace.
- No follow-up questions.
- No decorative wording.

OUTPUT JSON ONLY with exactly:
{
  "answer": "short factual synthesis",
  "sources": [
    { "title": "Source name", "url": "https://..." }
  ]
}

OUTPUT REQUIREMENTS
- "answer" must be directly usable by another medical assistant agent.
- "sources" should contain the strongest sources first.
- Prefer 3 to 6 strong sources when available.
- Keep source titles clean and specific.
"""


class MedicalWebSearchTool:
    def __init__(self, llm: LLMRuntime):
        self.llm = llm

    async def run(self, *, prompt: str, language: str = "fr") -> Dict[str, Any]:
        start_ts = time.time()

        if not isinstance(prompt, str) or not prompt.strip():
            return {
                "ok": False,
                "error": "EMPTY_WEB_SEARCH_PROMPT",
            }

        result = None
        meta: Dict[str, Any] = {}

        # 1) Tentative Perplexity / ordre par défaut du runtime
        try:
            result, meta = await self.llm.web_search_json(
                messages=[
                    {"role": "system", "content": SYSTEM_WEB_SEARCH_MEDICAL_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            meta["fallback_used"] = False
            meta["fallback_reason"] = None

        # 2) Si Perplexity répond mal (JSON cassé ou autre), fallback OpenAI
        except Exception as e:
            try:
                result, meta = await self.llm.web_search_json(
                    messages=[
                        {"role": "system", "content": SYSTEM_WEB_SEARCH_MEDICAL_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                    provider_allowlist={"openai"},
                    preferred_order=["openai"],
                )
                meta["fallback_used"] = True
                meta["fallback_reason"] = "perplexity_json_failed"

            except Exception as e2:
                return {
                    "ok": False,
                    "error": "WEB_SEARCH_BOTH_PROVIDERS_FAILED",
                    "details": {
                        "perplexity_error": str(e),
                        "openai_error": str(e2),
                    },
                }

        if not isinstance(result, dict):
            return {
                "ok": False,
                "error": "INVALID_MEDICAL_WEB_SEARCH_RESPONSE",
                "raw": result,
                "meta": meta,
            }

        answer = result.get("answer")
        sources = result.get("sources", [])

        if not isinstance(answer, str) or not answer.strip():
            return {
                "ok": False,
                "error": "MEDICAL_WEB_SEARCH_NO_ANSWER",
                "raw": result,
                "meta": meta,
            }

        if not isinstance(sources, list):
            sources = []

        return {
            "ok": True,
            "query": prompt,
            "answer": answer.strip(),
            "sources": sources,
            "debug": {
                "provider": meta.get("provider"),
                "model": meta.get("model"),
                "duration_ms": int((time.time() - start_ts) * 1000),
                "search_mode": "medical",
                "fallback_used": meta.get("fallback_used", False),
                "fallback_reason": meta.get("fallback_reason"),
            },
        }