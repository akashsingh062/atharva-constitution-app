from __future__ import annotations

import json
import os
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    from openai_client import (
        AtharvaConstitutionClient,
        AtharvaConstitutionError,
        ComparisonInput,
    )
    from prompting import DEFAULT_MODEL, DEFAULT_REASONING_EFFORT
else:
    from atharva_constitution_app.openai_client import (
        AtharvaConstitutionClient,
        AtharvaConstitutionError,
        ComparisonInput,
    )
    from atharva_constitution_app.prompting import (
        DEFAULT_MODEL,
        DEFAULT_REASONING_EFFORT,
    )

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/compare":
            self.send_error(HTTPStatus.NOT_FOUND, "Route not found.")
            return

        try:
            payload = self._read_json_body()
            user_input = self._build_input(payload)
            client = AtharvaConstitutionClient()
            result = client.compare(user_input)
            self._send_json(HTTPStatus.OK, {"ok": True, "result": result})
        except AtharvaConstitutionError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except json.JSONDecodeError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "Request body must be valid JSON."},
            )
        except Exception:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": "Unexpected server error."},
            )

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def _build_input(self, payload: dict[str, Any]) -> ComparisonInput:
        vedic_principle = str(payload.get("vedic_principle", "")).strip()
        constitutional_article = str(payload.get("constitutional_article", "")).strip()
        model = str(payload.get("model") or DEFAULT_MODEL).strip()
        reasoning_effort = str(
            payload.get("reasoning_effort") or DEFAULT_REASONING_EFFORT
        ).strip()

        if not vedic_principle or not constitutional_article:
            raise AtharvaConstitutionError(
                "Both the Vedic principle and the constitutional article are required."
            )

        return ComparisonInput(
            vedic_principle=vedic_principle,
            constitutional_article=constitutional_article,
            model=model,
            reasoning_effort=reasoning_effort,
        )

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run() -> None:
    port = int(os.environ.get("PORT", "8000"))
    handler = partial(AppHandler, directory=str(STATIC_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Atharva Constitution app running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
