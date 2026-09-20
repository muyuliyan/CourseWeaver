from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def clean_text(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    text = text.replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def split_text(text: str, size: int = 1800, overlap: int = 200):
    start = 0
    while start < len(text):
        yield text[start:start + size].strip()
        start += size - overlap


def build(course_dir: Path) -> int:
    manifest_path = course_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chunks = []
    for collection in manifest.get("collections", []):
        for item in collection.get("items", []):
            if not item.get("retrieval_enabled", True):
                continue
            source = course_dir / item["file"]
            if source.suffix.lower() not in {".md", ".txt"}:
                print(f"Skipping unsupported source: {source}")
                continue
            text = clean_text(source.read_text(encoding="utf-8"))
            for index, part in enumerate(split_text(text), start=1):
                if part:
                    chunks.append({
                        "id": f"{item['id']}-{index}",
                        "source_id": item["id"],
                        "title": item["title"],
                        "type": collection["id"],
                        "page": index,
                        "text": part,
                    })
    (course_dir / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(chunks)} chunks to {course_dir / 'chunks.json'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a CourseWeaver index from Markdown and text files.")
    parser.add_argument("course_dir", type=Path, help="Directory containing manifest.json")
    args = parser.parse_args()
    return build(args.course_dir.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
