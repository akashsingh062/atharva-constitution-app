from __future__ import annotations

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_REASONING_EFFORT = "low"

SYSTEM_PROMPT = """
You compare Atharva Vedic ideas with modern Indian constitutional principles.

Your job:
- Identify the most relevant shared ethical or philosophical themes
- Explain the connection in simple language
- Suggest a practical modern application

Rules:
- Treat the comparison as interpretive and philosophical, not as proof of direct legal derivation
- Do not exaggerate weak connections; if the overlap is limited, say so clearly
- Do not give legal advice or make sectarian claims
- Use plain, accessible English
- Keep the similarity concise
- Keep the explanation and application practical and easy to understand
- Return only JSON matching the schema
""".strip()

COMPARISON_SCHEMA = {
    "type": "object",
    "properties": {
        "themes": {
            "type": "array",
            "description": "Two to four short theme labels shared across both inputs.",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 4,
        },
        "similarity": {
            "type": "string",
            "description": "A brief statement of the main similarity.",
        },
        "explanation": {
            "type": "string",
            "description": "A simple explanation of the relationship between the two inputs.",
        },
        "application": {
            "type": "string",
            "description": "A real-world use or relevance in modern society.",
        },
    },
    "required": ["themes", "similarity", "explanation", "application"],
    "additionalProperties": False,
}


def build_user_message(vedic_principle: str, constitutional_article: str) -> str:
    return (
        "Compare the following two inputs.\n\n"
        f"Vedic Principle or Verse:\n{vedic_principle.strip()}\n\n"
        f"Constitutional Law or Article:\n{constitutional_article.strip()}\n\n"
        "Return the result using the required structure."
    )
