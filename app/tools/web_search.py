# app/tools/web_search.py
from __future__ import annotations

from typing import Any, Dict
import time

from app.llm.runtime import LLMRuntime


SYSTEM_WEB_SEARCH_PROMPT = """
You are a web research assistant.

Rules:
- Answer strictly based on reliable, up-to-date web sources.
- Be factual, neutral, concise.
- Do NOT add opinions.
- Do NOT give advice.
- Do NOT explain reasoning.
- Do NOT ask questions.

Output JSON ONLY with:
{
  "answer": "short factual answer",
  "sources": [
    { "title": "Source name", "url": "https://..." }
  ]
}
"""


class WebSearchTool:
    """
    Tool: Web Search
    Provider: Perplexity (sonar / sonar-pro)

    Input:
      - prompt (str) : web_search_prompt from Orchestrator
      - language (str)

    Output:
      {
        ok: bool,
        answer: str,
        sources: list,
        debug: dict
      }
    """

    def __init__(self, llm: LLMRuntime):
        self.llm = llm

    async def run(self, *, prompt: str, language: str = "fr") -> Dict[str, Any]:
        start_ts = time.time()

        # --- Guardrail input ---
        if not isinstance(prompt, str) or not prompt.strip():
            return {
                "ok": False,
                "error": "EMPTY_WEB_SEARCH_PROMPT",
            }

        # --- Call Perplexity ---
        result, meta = await self.llm.chat_json(
            messages=[
                {"role": "system", "content": SYSTEM_WEB_SEARCH_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        # --- Validate output ---
        if not isinstance(result, dict):
            return {
                "ok": False,
                "error": "INVALID_WEB_SEARCH_RESPONSE",
                "raw": result,
                "meta": meta,
            }

        answer = result.get("answer")
        sources = result.get("sources", [])

        if not isinstance(answer, str) or not answer.strip():
            return {
                "ok": False,
                "error": "WEB_SEARCH_NO_ANSWER",
                "raw": result,
                "meta": meta,
            }

        if not isinstance(sources, list):
            sources = []

        # --- Final output ---
        return {
            "ok": True,
            "query": prompt,
            "answer": answer.strip(),
            "sources": sources,
            "debug": {
                "provider": "perplexity",
                "model": meta.get("model"),
                "duration_ms": int((time.time() - start_ts) * 1000),
            },
        }