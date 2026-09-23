from __future__ import annotations

import json
import mimetypes
import os
import re
from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from providers import create_provider


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DEFAULT_SETTINGS = ROOT / "config" / "settings.example.json"
LOCAL_SETTINGS = ROOT / "config" / "settings.local.json"
DEFAULT_COURSE_PATH = "examples/compiler-foundations"
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{1,}|[\u4e00-\u9fff]{1,4}")


def read_json(path: Path, fallback=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def load_settings() -> dict:
    path = Path(os.environ.get("COURSEWEAVER_CONFIG", LOCAL_SETTINGS))
    settings = read_json(path) if path.is_file() else read_json(DEFAULT_SETTINGS, {})
    settings = settings or {}
    server = settings.setdefault("server", {})
    agent = settings.setdefault("agent", {})
    server["host"] = os.environ.get("COURSEWEAVER_HOST", server.get("host", "127.0.0.1"))
    server["port"] = int(os.environ.get("COURSEWEAVER_PORT", server.get("port", 8143)))
    if os.environ.get("COURSEWEAVER_COURSE_PATH"):
        settings["course_path"] = os.environ["COURSEWEAVER_COURSE_PATH"]
    if os.environ.get("COURSEWEAVER_API_KEY"):
        agent["api_key"] = os.environ["COURSEWEAVER_API_KEY"]
    if os.environ.get("COURSEWEAVER_MODEL"):
        agent["model"] = os.environ["COURSEWEAVER_MODEL"]
    return settings


SETTINGS = load_settings()
COURSE_ROOT = (ROOT / SETTINGS.get("course_path", DEFAULT_COURSE_PATH)).resolve()
MANIFEST = COURSE_ROOT / "manifest.json"
CHUNKS = COURSE_ROOT / "chunks.json"
TUTOR = COURSE_ROOT / "tutor.md"


def terms(text: str) -> Counter:
    return Counter(token.lower() for token in TOKEN_RE.findall(text))


def retrieve(query: str, limit: int | None = None) -> list[dict]:
    query_terms = terms(query)
    if not query_terms:
        return []
    scored = []
    for chunk in read_json(CHUNKS, []):
        body_terms = terms(chunk.get("text", ""))
        overlap = sum(min(count, body_terms.get(term, 0)) for term, count in query_terms.items())
        phrase_bonus = 4 if query.lower() in chunk.get("text", "").lower() else 0
        if overlap + phrase_bonus:
            scored.append((overlap + phrase_bonus, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    configured_limit = SETTINGS.get("retrieval", {}).get("max_chunks", 6)
    return [chunk for _, chunk in scored[: limit or configured_limit]]


def build_prompt(message: str, history: list[dict], context: list[dict]) -> str:
    excerpts = "\n\n".join(
        f"[{item['source_id']}, p. {item.get('page', 1)}] {item['title']}\n{item['text']}"
        for item in context
    ) or "No relevant local excerpt was found."
    conversation = "\n".join(
        f"{item.get('role', 'user').upper()}: {str(item.get('content', ''))[:3000]}"
        for item in history[-8:]
    )
    return (
        f"Conversation so far:\n{conversation}\n\n"
        f"Student's new message:\n{message}\n\n"
        f"Retrieved course excerpts:\n{excerpts}"
    )


def call_agent(message: str, history: list[dict]) -> tuple[str, list[dict]]:
    agent = SETTINGS.get("agent", {})
    context = retrieve(message)
    instructions = TUTOR.read_text(encoding="utf-8")
    answer = create_provider(agent).generate(instructions, build_prompt(message, history, context))
    sources = [
        {"id": item["source_id"], "title": item["title"], "page": item.get("page", 1)}
        for item in context
    ]
    return answer, sources


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean = urlparse(path).path.lstrip("/")
        if ".." in Path(clean).parts:
            return str(STATIC / "__not_found__")
        if clean.startswith("materials/"):
            candidate = (COURSE_ROOT / clean.removeprefix("materials/")).resolve()
            if COURSE_ROOT not in candidate.parents:
                return str(STATIC / "__not_found__")
            return str(candidate)
        return str(STATIC / (clean or "index.html"))

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/course":
            return self.send_json(read_json(MANIFEST, {"course": {}, "collections": []}))
        if route == "/api/status":
            agent = SETTINGS.get("agent", {})
            return self.send_json({
                "ready": bool(read_json(CHUNKS, [])),
                "agent_configured": bool(agent.get("api_key") and agent.get("api_key") != "replace-me"),
                "provider": agent.get("provider", "openai_responses"),
                "model": agent.get("model", ""),
                "chunks": len(read_json(CHUNKS, [])),
            })
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            return self.send_json({"error": "Not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            message = str(payload.get("message", "")).strip()
            if not message:
                return self.send_json({"error": "Message cannot be empty."}, 400)
            answer, sources = call_agent(message, payload.get("history", []))
            return self.send_json({"answer": answer, "sources": sources})
        except Exception as exc:
            return self.send_json({"error": str(exc)}, 500)


def main():
    server = SETTINGS.get("server", {})
    host, port = server.get("host", "127.0.0.1"), int(server.get("port", 8143))
    mimetypes.add_type("application/javascript", ".js")
    title = read_json(MANIFEST, {}).get("course", {}).get("title", "CourseWeaver")
    print(f"CourseWeaver ({title}) running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()

