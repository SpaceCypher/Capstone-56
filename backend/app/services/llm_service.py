import asyncio
import json
import os
import random
from typing import Any

import httpx


class LLMServiceError(RuntimeError):
    pass


class LLMRateLimitError(LLMServiceError):
    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def _parse_retry_after_seconds(response: httpx.Response) -> float | None:
    retry_after_raw = response.headers.get("Retry-After")
    if not retry_after_raw:
        return None

    try:
        retry_after = float(retry_after_raw)
    except ValueError:
        return None

    if retry_after < 0:
        return None
    return retry_after


def _extract_provider_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:300] if response.text else ""

    if isinstance(payload, dict):
        error_obj = payload.get("error")
        if isinstance(error_obj, dict):
            message = error_obj.get("message")
            if isinstance(message, str):
                return message
        message = payload.get("message")
        if isinstance(message, str):
            return message
    return ""


def _build_rate_limit_error(response: httpx.Response) -> LLMRateLimitError:
    retry_after = _parse_retry_after_seconds(response)
    provider_message = _extract_provider_error_message(response)
    detail = f" Provider message: {provider_message}" if provider_message else ""
    return LLMRateLimitError(
        f"AI provider is rate-limiting requests. Please retry in a moment.{detail}",
        retry_after=retry_after,
    )


def _extract_json(content: str) -> dict[str, Any]:
    cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMServiceError("LLM response did not contain valid JSON object")

    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMServiceError("Failed to parse JSON from LLM response") from exc

    if not isinstance(parsed, dict):
        raise LLMServiceError("LLM response JSON is not an object")
    return parsed


async def call_llm(prompt: str) -> dict[str, Any]:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    api_key = groq_api_key or os.getenv("LLM_API_KEY", "").strip() or google_api_key
    if not api_key:
        raise LLMServiceError("Missing GROQ_API_KEY or LLM_API_KEY")

    base_url = os.getenv("LLM_BASE_URL", "").strip()
    if not base_url:
        if groq_api_key:
            base_url = "https://api.groq.com/openai/v1"
        elif google_api_key:
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        else:
            base_url = "https://api.openai.com/v1"

    llm_model = os.getenv("LLM_MODEL", "").strip()
    llm_fallback_model = os.getenv("LLM_FALLBACK_MODEL", "").strip()
    if groq_api_key:
        model = os.getenv("GROQ_MODEL", "").strip() or llm_model or "llama-3.1-8b-instant"
        fallback_model = os.getenv("GROQ_FALLBACK_MODEL", "").strip() or llm_fallback_model
    elif google_api_key:
        model = os.getenv("GOOGLE_MODEL", "").strip() or llm_model or "gemini-1.5-flash"
        fallback_model = os.getenv("GOOGLE_FALLBACK_MODEL", "").strip() or llm_fallback_model
    else:
        model = llm_model or "gpt-4o-mini"
        fallback_model = llm_fallback_model
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    retries = int(os.getenv("LLM_MAX_RETRIES", "4"))
    base_backoff = float(os.getenv("LLM_RETRY_BASE_SECONDS", "0.8"))

    url = f"{base_url}/chat/completions"

    base_body = {
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You are a precise tutoring assistant. Always return strict JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async def _call_model(client: httpx.AsyncClient, selected_model: str) -> dict[str, Any]:
        body = {**base_body, "model": selected_model}

        attempt = 0
        last_error: Exception | None = None
        while attempt <= retries:
            try:
                response = await client.post(url, headers=headers, json=body)
                response.raise_for_status()
                payload = response.json()

                content = payload["choices"][0]["message"]["content"]
                if not isinstance(content, str):
                    raise LLMServiceError("LLM content is not text")
                return _extract_json(content)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code

                if status == 429:
                    retry_after = _parse_retry_after_seconds(exc.response)
                    if attempt < retries:
                        delay = retry_after if retry_after is not None else base_backoff * (2**attempt)
                        jitter = random.uniform(0.0, 0.15 * max(delay, 0.1))
                        await asyncio.sleep(delay + jitter)
                        attempt += 1
                        continue
                    raise _build_rate_limit_error(exc.response) from exc

                if 500 <= status < 600 and attempt < retries:
                    delay = base_backoff * (2**attempt)
                    jitter = random.uniform(0.0, 0.15 * delay)
                    await asyncio.sleep(delay + jitter)
                    attempt += 1
                    continue

                provider_message = _extract_provider_error_message(exc.response)
                detail = f" Provider message: {provider_message}" if provider_message else ""
                raise LLMServiceError(f"LLM provider returned HTTP {status}.{detail}") from exc
            except (httpx.RequestError, KeyError, ValueError, LLMServiceError) as exc:
                last_error = exc
                if attempt == retries:
                    break
                delay = base_backoff * (2**attempt)
                jitter = random.uniform(0.0, 0.15 * delay)
                await asyncio.sleep(delay + jitter)
                attempt += 1

        if isinstance(last_error, httpx.HTTPStatusError) and last_error.response.status_code == 429:
            raise _build_rate_limit_error(last_error.response) from last_error
        raise LLMServiceError("LLM call failed after retries") from last_error

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            return await _call_model(client, model)
        except LLMRateLimitError:
            if fallback_model and fallback_model != model:
                return await _call_model(client, fallback_model)
            raise
