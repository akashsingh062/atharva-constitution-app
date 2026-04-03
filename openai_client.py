from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

if __package__ in {None, ""}:
    from prompting import (
        COMPARISON_SCHEMA,
        DEFAULT_MODEL,
        DEFAULT_REASONING_EFFORT,
        SYSTEM_PROMPT,
        build_user_message,
    )
else:
    from atharva_constitution_app.prompting import (
        COMPARISON_SCHEMA,
        DEFAULT_MODEL,
        DEFAULT_REASONING_EFFORT,
        SYSTEM_PROMPT,
        build_user_message,
    )

OPENAI_API_URL = "https://api.openai.com/v1/responses"
GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_local_env()


class AtharvaConstitutionError(Exception):
    """Raised when the comparison request cannot be completed."""


@dataclass(slots=True)
class ComparisonInput:
    vedic_principle: str
    constitutional_article: str
    model: str = DEFAULT_MODEL
    reasoning_effort: str = DEFAULT_REASONING_EFFORT


def build_openai_response_payload(user_input: ComparisonInput) -> dict[str, Any]:
    return {
        "model": user_input.model,
        "reasoning": {"effort": user_input.reasoning_effort},
        "store": False,
        "max_output_tokens": 500,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_message(
                    user_input.vedic_principle,
                    user_input.constitutional_article,
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "atharva_constitution_comparison",
                "schema": COMPARISON_SCHEMA,
                "strict": True,
            }
        },
    }


def build_gemini_response_payload(user_input: ComparisonInput) -> dict[str, Any]:
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": build_user_message(
                            user_input.vedic_principle,
                            user_input.constitutional_article,
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": COMPARISON_SCHEMA,
            "maxOutputTokens": 1024,
        },
    }

    thinking_config = build_gemini_thinking_config(
        user_input.model, user_input.reasoning_effort
    )
    if thinking_config:
        payload["generationConfig"]["thinkingConfig"] = thinking_config

    return payload


def build_gemini_thinking_config(
    model: str, reasoning_effort: str
) -> dict[str, Any] | None:
    normalized_model = model.removeprefix("models/")

    if normalized_model.startswith("gemini-3"):
        level_by_effort = {"low": "low", "medium": "medium", "high": "high"}
        return {"thinkingLevel": level_by_effort.get(reasoning_effort, "low")}

    if normalized_model.startswith("gemini-2.5-pro"):
        budget_by_effort = {"low": 128, "medium": 512, "high": 2048}
        return {"thinkingBudget": budget_by_effort.get(reasoning_effort, 512)}

    if normalized_model.startswith("gemini-2.5"):
        budget_by_effort = {"low": 0, "medium": 256, "high": 1024}
        return {"thinkingBudget": budget_by_effort.get(reasoning_effort, 0)}

    return None


def build_response_payload(user_input: ComparisonInput) -> dict[str, Any]:
    return build_openai_response_payload(user_input)


def _extract_openai_structured_output(response_data: dict[str, Any]) -> dict[str, Any]:
    if response_data.get("error"):
        message = response_data["error"].get("message", "Unknown API error.")
        raise AtharvaConstitutionError(message)

    for output_item in response_data.get("output", []):
        if output_item.get("type") != "message":
            continue

        for content_item in output_item.get("content", []):
            content_type = content_item.get("type")
            if content_type == "refusal":
                raise AtharvaConstitutionError(
                    content_item.get("refusal", "The model refused the request.")
                )
            if content_type == "output_text":
                try:
                    return json.loads(content_item["text"])
                except (KeyError, json.JSONDecodeError) as exc:
                    raise AtharvaConstitutionError(
                        "The model response was not valid JSON."
                    ) from exc

    raise AtharvaConstitutionError("No structured output was returned by the API.")


def _extract_gemini_structured_output(response_data: dict[str, Any]) -> dict[str, Any]:
    if response_data.get("error"):
        message = response_data["error"].get("message", "Unknown API error.")
        raise AtharvaConstitutionError(message)

    prompt_feedback = response_data.get("promptFeedback", {})
    if prompt_feedback.get("blockReason"):
        raise AtharvaConstitutionError(
            f"Gemini blocked the prompt: {prompt_feedback['blockReason']}."
        )

    candidates = response_data.get("candidates", [])
    if not candidates:
        raise AtharvaConstitutionError("No structured output was returned by Gemini.")

    candidate = candidates[0]
    finish_reason = candidate.get("finishReason")
    if finish_reason and finish_reason not in {"STOP", "MAX_TOKENS"}:
        raise AtharvaConstitutionError(
            candidate.get("finishMessage")
            or f"Gemini stopped the response: {finish_reason}."
        )

    text_parts = []
    for part in candidate.get("content", {}).get("parts", []):
        if "text" in part:
            text_parts.append(part["text"])

    if not text_parts:
        raise AtharvaConstitutionError("Gemini returned no text content.")

    try:
        return json.loads("".join(text_parts))
    except json.JSONDecodeError as exc:
        raise AtharvaConstitutionError(
            "Gemini returned a response that was not valid JSON."
        ) from exc


def extract_structured_output(response_data: dict[str, Any]) -> dict[str, Any]:
    if "output" in response_data:
        return _extract_openai_structured_output(response_data)
    return _extract_gemini_structured_output(response_data)


class AtharvaConstitutionClient:
    def __init__(
        self,
        api_key: str | None = None,
        google_api_key: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.google_api_key = (
            google_api_key
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )

    def _choose_provider(self, model: str) -> str:
        if model.startswith("gemini-") or model.startswith("models/gemini-"):
            return "gemini"
        if model.startswith("gpt-"):
            return "openai"
        if self.google_api_key and not self.api_key:
            return "gemini"
        return "openai"

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        http_request = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8")
            try:
                parsed = json.loads(details)
                message = parsed.get("error", {}).get("message", details)
            except json.JSONDecodeError:
                message = details or str(exc)
            raise AtharvaConstitutionError(message) from exc
        except error.URLError as exc:
            raise AtharvaConstitutionError(
                "Unable to reach the model API. Check your network connection."
            ) from exc

    def compare(self, user_input: ComparisonInput) -> dict[str, Any]:
        provider = self._choose_provider(user_input.model)

        if provider == "gemini":
            if not self.google_api_key:
                raise AtharvaConstitutionError(
                    "GOOGLE_API_KEY or GEMINI_API_KEY is not set. Add it to your environment and try again."
                )
            model = user_input.model.removeprefix("models/")
            response_data = self._post_json(
                GEMINI_API_URL_TEMPLATE.format(model=model),
                build_gemini_response_payload(user_input),
                {
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.google_api_key,
                },
            )
            return extract_structured_output(response_data)

        if not self.api_key:
            raise AtharvaConstitutionError(
                "OPENAI_API_KEY is not set. Add it to your environment and try again."
            )

        response_data = self._post_json(
            OPENAI_API_URL,
            build_openai_response_payload(user_input),
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        return extract_structured_output(response_data)
