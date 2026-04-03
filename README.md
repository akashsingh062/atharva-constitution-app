# Atharva Veda vs Indian Constitution App

This mini-app compares an Atharva Vedic principle or verse with an Indian constitutional article and returns:

- `Similarity`
- `Explanation`
- `Application`

It uses structured JSON output with either the Google Gemini API or the OpenAI Responses API, then renders the result in a small local web UI.

## Files

- `app.py`: local HTTP server
- `openai_client.py`: provider client for Gemini or OpenAI
- `prompting.py`: task prompt and JSON schema
- `static/`: frontend assets

## Run

Start the app from the workspace root:

```bash
export GOOGLE_API_KEY=your_key_here
python3 app.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Notes

- Default model: `gemini-2.5-flash`
- Default reasoning effort: `low`
- The comparison is designed to stay philosophical and interpretive, not legal-advisory
- The backend uses stdlib HTTP calls, so no extra Python package is required
- You can also use `GEMINI_API_KEY` instead of `GOOGLE_API_KEY`, or `OPENAI_API_KEY` with a `gpt-*` model
