from __future__ import annotations

import json
import math
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
ASCII_TERM_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+-]*")
CHINESE_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
DOCUMENT_REF_RE = re.compile(r"\b(lecture|lec|pa|wa|lab)[\s._/-]*0*(\d+)\b", re.IGNORECASE)
CHINESE_LECTURE_RE = re.compile(r"第?\s*([零〇一二两三四五六七八九十百\d]+)\s*(?:讲|课)")


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
    tokens = [token.lower() for token in ASCII_TERM_RE.findall(text)]
    for run in CHINESE_RUN_RE.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[index:index + 2] for index in range(len(run) - 1))
    return Counter(tokens)


def course_items() -> list[dict]:
    items = []
    for collection in read_json(MANIFEST, {}).get("collections", []):
        for item in collection.get("items", []):
            items.append({**item, "collection_id": collection.get("id", "")})
    return items


def compact_reference(text: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", text.lower())


def chinese_number(text: str) -> int | None:
    if text.isdigit():
        return int(text)
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if text == "十":
        return 10
    if "十" in text:
        left, right = text.split("十", 1)
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return tens * 10 + ones
    if len(text) == 1:
        return digits.get(text)
    return None


def resolve_source_ids(query: str, items: list[dict] | None = None) -> set[str]:
    items = items or course_items()
    by_id = {item["id"].lower(): item["id"] for item in items}
    resolved = set()

    prefixes = {"lecture": "lecture", "lec": "lecture", "pa": "pa", "wa": "wa",
                "lab": "local-lab"}
    for prefix, number in DOCUMENT_REF_RE.findall(query):
        canonical_prefix = prefixes[prefix.lower()]
        candidate = f"{canonical_prefix}-{int(number):02d}"
        if candidate in by_id:
            resolved.add(by_id[candidate])

    for number_text in CHINESE_LECTURE_RE.findall(query):
        number = chinese_number(number_text)
        candidate = f"lecture-{number:02d}" if number is not None else ""
        if candidate in by_id:
            resolved.add(by_id[candidate])

    compact_query = compact_reference(query)
    for item in items:
        aliases = {item.get("id", ""), item.get("title", ""), item.get("file", ""),
                   Path(item.get("file", "")).name, Path(item.get("file", "")).stem}
        if item.get("display_file"):
            aliases.update({item["display_file"], Path(item["display_file"]).name,
                            Path(item["display_file"]).stem})
        for alias in aliases:
            compact_alias = compact_reference(alias)
            if len(compact_alias) >= 5 and compact_alias in compact_query:
                resolved.add(item["id"])
                break
    return resolved


def retrieval_query(message: str, history: list[dict]) -> str:
    if resolve_source_ids(message):
        return message
    prior_user_messages = [
        str(item.get("content", ""))[:500]
        for item in history[-6:]
        if item.get("role") == "user" and item.get("content")
    ]
    return " ".join(prior_user_messages[-2:] + [message])


def retrieve(
    query: str,
    limit: int | None = None,
    history: list[dict] | None = None,
    active_source_id: str | None = None,
) -> list[dict]:
    history = history or []
    expanded_query = retrieval_query(query, history)
    query_terms = terms(expanded_query)
    if not query_terms and not active_source_id:
        return []
    chunks = read_json(CHUNKS, [])
    requested_sources = resolve_source_ids(expanded_query)
    if requested_sources:
        chunks = [chunk for chunk in chunks if chunk.get("source_id") in requested_sources]
    if not chunks:
        return []

    document_terms = []
    document_frequencies = Counter()
    for chunk in chunks:
        body = terms(chunk.get("text", ""))
        document_terms.append(body)
        document_frequencies.update(body.keys())

    average_length = max(1.0, sum(sum(body.values()) for body in document_terms) / len(document_terms))
    scored = []
    for position, (chunk, body_terms) in enumerate(zip(chunks, document_terms)):
        body_length = max(1, sum(body_terms.values()))
        score = 0.0
        for term, query_count in query_terms.items():
            frequency = body_terms.get(term, 0)
            if not frequency:
                continue
            inverse_frequency = math.log(1 + (len(chunks) - document_frequencies[term] + 0.5)
                                         / (document_frequencies[term] + 0.5))
            saturation = frequency * 2.2 / (frequency + 1.2 * (0.25 + 0.75 * body_length / average_length))
            score += inverse_frequency * saturation * min(query_count, 2)

        metadata = " ".join(str(chunk.get(field, "")) for field in
                            ("source_id", "title", "file", "display_file", "collection"))
        metadata_terms = terms(metadata)
        score += 2.5 * sum(1 for term in query_terms if term in metadata_terms)
        if query.lower() in chunk.get("text", "").lower():
            score += 4
        if requested_sources and chunk.get("source_id") in requested_sources:
            score += 20
        elif active_source_id and chunk.get("source_id") == active_source_id:
            score += 8
        if score > 0:
            scored.append((score, -position, chunk))
    scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
    configured_limit = SETTINGS.get("retrieval", {}).get("max_chunks", 6)
    result_limit = limit or configured_limit
    if requested_sources or active_source_id:
        return [chunk for _, _, chunk in scored[:result_limit]]

    selected = []
    source_counts = Counter()
    for _, _, chunk in scored:
        source_id = chunk.get("source_id", "")
        if source_counts[source_id] >= 2:
            continue
        selected.append(chunk)
        source_counts[source_id] += 1
        if len(selected) >= result_limit:
            break
    return selected


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


def call_agent(
    message: str,
    history: list[dict],
    active_source_id: str | None = None,
) -> tuple[str, list[dict]]:
    agent = SETTINGS.get("agent", {})
    context = retrieve(message, history=history, active_source_id=active_source_id)
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

    def guess_type(self, path):
        if path.lower().endswith((".txt", ".md")):
            return "text/plain; charset=utf-8"
        return super().guess_type(path)

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
            answer, sources = call_agent(
                message,
                payload.get("history", []),
                str(payload.get("active_material_id", "")).strip() or None,
            )
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

