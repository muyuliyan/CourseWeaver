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


def item_chunks(item: dict, collection: dict, raw_text: str):
    paged = "\f" in raw_text
    units = raw_text.split("\f") if paged else [raw_text]
    excerpt_number = 0
    for page_number, unit in enumerate(units, start=1):
        text = clean_text(unit)
        for part_number, part in enumerate(split_text(text), start=1):
            if not part:
                continue
            excerpt_number += 1
            if paged:
                chunk_id = f"{item['id']}-p{page_number}-c{part_number}"
                locator = page_number
            else:
                chunk_id = f"{item['id']}-{excerpt_number}"
                locator = excerpt_number
            yield {
                "id": chunk_id,
                "source_id": item["id"],
                "title": item["title"],
                "type": collection["id"],
                "collection": collection.get("title", collection["id"]),
                "file": item["file"],
                "display_file": item.get("display_file", ""),
                "page": locator,
                "text": part,
            }


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
            chunks.extend(item_chunks(item, collection, source.read_text(encoding="utf-8")))
    output_path = course_dir / "chunks.json"
    with output_path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(chunks, ensure_ascii=False, indent=2))
        output.write("\n")
    print(f"Wrote {len(chunks)} chunks to {output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a CourseWeaver index from Markdown and text files.")
    parser.add_argument("course_dir", type=Path, help="Directory containing manifest.json")
    args = parser.parse_args()
    return build(args.course_dir.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
