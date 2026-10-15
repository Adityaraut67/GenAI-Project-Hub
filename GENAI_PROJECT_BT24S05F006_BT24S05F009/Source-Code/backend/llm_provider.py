import json
import urllib.error
import urllib.request
from typing import Any, Dict, List

from config import get_llm_settings
from rag import build_grounded_prompt, build_local_document_answer


class LLMProviderError(RuntimeError):
    pass


def _build_openai_payload(prompt: str, model: str, temperature: float = 0.2) -> Dict[str, Any]:
    return {
        "model": model,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": "You are CivicLens AI, an informational assistant that helps users understand public government information using retrieved evidence. Use the evidence carefully, never invent facts, and clearly distinguish verified information from unverified information.",
            },
            {"role": "user", "content": prompt},
        ],
    }


def generate_answer(question: str, context: List[Dict[str, Any]], language: str = "en") -> Dict[str, Any]:
    settings = get_llm_settings()
    api_key = (settings.get("api_key") or "").strip()
    citations = [
        {
            "title": item.get("title") or item.get("name") or "Source",
            "url": item.get("url"),
            "content": item.get("content", "")[:280],
            "metadata": item.get("metadata", {}),
        }
        for item in context
    ]

    if not api_key:
        return {
            "available": False,
            "answer": build_local_document_answer(question, context),
            "citations": citations,
        }

    prompt = build_grounded_prompt(question, context, language)
    payload = _build_openai_payload(prompt, settings["model"])
    request = urllib.request.Request(
        url=settings["endpoint"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise LLMProviderError("Authentication failed for the configured AI provider.") from exc
        if exc.code == 429:
            raise LLMProviderError("The configured AI provider rate limit was reached.") from exc
        raise LLMProviderError(f"The AI provider returned an HTTP error: {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise LLMProviderError("A network error occurred while contacting the AI provider.") from exc
    except TimeoutError as exc:
        raise LLMProviderError("The AI request timed out.") from exc

    try:
        answer = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("The AI provider returned an unexpected response payload.") from exc

    return {"available": True, "answer": answer, "citations": citations}
