from __future__ import annotations

import unittest

from atharva_constitution_app.openai_client import (
    AtharvaConstitutionError,
    AtharvaConstitutionClient,
    ComparisonInput,
    build_gemini_response_payload,
    build_gemini_thinking_config,
    build_openai_response_payload,
    extract_structured_output,
)


class OpenAIClientTests(unittest.TestCase):
    def test_build_openai_response_payload_uses_structured_outputs(self) -> None:
        payload = build_openai_response_payload(
            ComparisonInput(
                vedic_principle="Dharma as justice and duty.",
                constitutional_article="Article 14 equality before law.",
            )
        )

        self.assertEqual(payload["model"], "gemini-2.5-flash")
        self.assertEqual(payload["reasoning"]["effort"], "low")
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(
            payload["text"]["format"]["name"], "atharva_constitution_comparison"
        )

    def test_build_gemini_response_payload_uses_structured_outputs(self) -> None:
        payload = build_gemini_response_payload(
            ComparisonInput(
                vedic_principle="Dharma as justice and duty.",
                constitutional_article="Article 14 equality before law.",
            )
        )

        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(
            payload["generationConfig"]["responseJsonSchema"]["type"], "object"
        )
        self.assertEqual(payload["generationConfig"]["thinkingConfig"]["thinkingBudget"], 0)
        self.assertEqual(payload["contents"][0]["role"], "user")

    def test_build_gemini_thinking_config_uses_budget_for_gemini_25_flash(self) -> None:
        self.assertEqual(
            build_gemini_thinking_config("gemini-2.5-flash", "medium"),
            {"thinkingBudget": 256},
        )

    def test_extract_structured_output_returns_json_payload_from_openai(self) -> None:
        response_data = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": (
                                '{"themes":["fairness","equality"],'
                                '"similarity":"Both stress fairness.",'
                                '"explanation":"They both value equal treatment.",'
                                '"application":"They support anti-discrimination."}'
                            ),
                        }
                    ],
                }
            ]
        }

        parsed = extract_structured_output(response_data)
        self.assertEqual(parsed["themes"], ["fairness", "equality"])
        self.assertEqual(parsed["similarity"], "Both stress fairness.")

    def test_extract_structured_output_returns_json_payload_from_gemini(self) -> None:
        response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    '{"themes":["fairness","equality"],'
                                    '"similarity":"Both stress fairness.",'
                                    '"explanation":"They both value equal treatment.",'
                                    '"application":"They support anti-discrimination."}'
                                )
                            }
                        ]
                    },
                    "finishReason": "STOP",
                }
            ]
        }

        parsed = extract_structured_output(response_data)
        self.assertEqual(parsed["themes"], ["fairness", "equality"])
        self.assertEqual(parsed["application"], "They support anti-discrimination.")

    def test_extract_structured_output_raises_on_refusal(self) -> None:
        response_data = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "refusal", "refusal": "Cannot comply."}],
                }
            ]
        }

        with self.assertRaises(AtharvaConstitutionError):
            extract_structured_output(response_data)

    def test_extract_structured_output_raises_on_gemini_prompt_block(self) -> None:
        response_data = {"promptFeedback": {"blockReason": "SAFETY"}}

        with self.assertRaises(AtharvaConstitutionError):
            extract_structured_output(response_data)

    def test_client_prefers_gemini_for_gemini_models(self) -> None:
        client = AtharvaConstitutionClient(api_key="openai-key", google_api_key="google-key")
        self.assertEqual(client._choose_provider("gemini-2.5-flash"), "gemini")


if __name__ == "__main__":
    unittest.main()
