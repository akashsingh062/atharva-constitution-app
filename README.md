# Atharva Veda vs Indian Constitution

<p align="center">
  A small AI web app that compares an Atharva Vedic principle with an Indian constitutional article and turns the overlap into a clear, structured explanation.
</p>

<p align="center">
  <strong>Gemini-ready</strong> · <strong>OpenAI-compatible</strong> · <strong>No external Python packages</strong>
</p>

## Overview

This project takes two inputs:

- an Atharva Vedic principle or verse
- an Indian constitutional article or legal principle

It then generates a structured comparison with:

- `themes`
- `similarity`
- `explanation`
- `application`

The output is intentionally philosophical and interpretive. It is not designed to make legal claims, historical claims of direct derivation, or legal-advisory judgments.

## Why It Feels Different

- Clean local web UI with guided inputs and sample prompts
- Structured JSON output instead of loose free-form text
- Works with `GOOGLE_API_KEY`, `GEMINI_API_KEY`, or `OPENAI_API_KEY`
- Uses only Python standard library networking and HTTP serving
- Simple enough to run locally in seconds

## How It Works

1. The frontend collects a Vedic principle and a constitutional reference.
2. The backend builds a constrained prompt plus JSON schema.
3. The app sends the request to Gemini or OpenAI, depending on model and available keys.
4. The response is validated and rendered into a readable card layout.

## Quick Start

Run from the project folder:

```bash
export GOOGLE_API_KEY=your_key_here
python3 app.py
```

Then open:

```text
http://127.0.0.1:8000
```

If port `8000` is busy, run on another port:

```bash
PORT=8010 python3 app.py
```

## Supported API Keys

The backend accepts any one of these:

- `GOOGLE_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

Default behavior:

- Default model: `gemini-2.5-flash`
- Default reasoning effort: `low`

If you select a `gpt-*` model, the app uses OpenAI. If you select a `gemini-*` model, the app uses Gemini.

## Example Use Case

**Input**

- Vedic Principle: `Dharma as justice, fairness, and moral duty in social life`
- Constitutional Article: `Article 14: Equality before law and equal protection of the laws`

**Output Shape**

```json
{
  "themes": ["Justice", "Equality", "Moral Duty"],
  "similarity": "Both ideas emphasize fairness and just treatment.",
  "explanation": "The comparison connects ethical duty with equality under law.",
  "application": "It can support civic education around fairness and equal rights."
}
```

## Project Structure

```text
atharva_constitution_app/
├── app.py
├── openai_client.py
├── prompting.py
├── static/
│   ├── app.js
│   ├── index.html
│   └── styles.css
└── test_openai_client.py
```

## Core Files

- `app.py` runs the local HTTP server and API route
- `openai_client.py` handles Gemini and OpenAI requests
- `prompting.py` defines the system prompt and JSON schema
- `static/` contains the frontend UI
- `test_openai_client.py` covers payload construction and response parsing

## Development

Run tests:

```bash
python3 -m unittest atharva_constitution_app.test_openai_client
```

## Notes

- The app is built for interpretive civic and ethical comparison, not legal advice.
- The backend uses the Python standard library, so there is no dependency install step.
- A local `.env` file can also be used for API keys during development.

## Future Improvements

- Add saved comparison history
- Export results as markdown or PDF
- Add side-by-side citation display
- Support more curated example datasets
