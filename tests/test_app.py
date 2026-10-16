import json
import os
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

os.environ["COURSEWEAVER_CONFIG"] = str(
    Path(__file__).resolve().parent.parent / "config" / "settings.example.json"
)

import app
from providers import OpenAICompatibleChatProvider, OpenAIResponsesProvider, create_provider
from scripts.build_index import clean_text, item_chunks


class CourseWeaverTests(unittest.TestCase):
    def test_default_example_is_self_contained(self):
        manifest = json.loads(app.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["course"]["license"], "MIT")
        self.assertGreaterEqual(len(manifest["collections"]), 2)
        for collection in manifest["collections"]:
            for item in collection["items"]:
                self.assertTrue((app.COURSE_ROOT / item["file"]).is_file())

    def test_retrieval_returns_course_evidence(self):
        results = app.retrieve("lexer tokens longest match")
        self.assertTrue(results)
        self.assertEqual(results[0]["source_id"], "lesson-01")

    def test_terms_keep_document_numbers(self):
        self.assertEqual(app.terms("Lecture 1")["1"], 1)

    def test_document_references_resolve_ids_and_filenames(self):
        items = [{
            "id": "lecture-01",
            "title": "Course Overview",
            "file": "lectures/lecture-01.txt",
            "display_file": "pdf/lectures/lecture01.pdf",
        }]
        for query in ("Lecture 1", "lecture01.pdf", "第一讲", "Course Overview"):
            self.assertEqual(app.resolve_source_ids(query, items), {"lecture-01"})

    def test_active_material_is_retrieved_for_contextual_question(self):
        results = app.retrieve("What does this mean?", active_source_id="lesson-02")
        self.assertTrue(results)
        self.assertEqual(results[0]["source_id"], "lesson-02")

    def test_follow_up_retrieval_uses_recent_user_history(self):
        history = [{"role": "user", "content": "lexer tokens longest match"}]
        results = app.retrieve("Explain that", history=history)
        self.assertTrue(results)
        self.assertEqual(results[0]["source_id"], "lesson-01")

    def test_provider_selection(self):
        self.assertIsInstance(create_provider({"provider": "openai_responses"}), OpenAIResponsesProvider)
        self.assertIsInstance(create_provider({"provider": "openai_compatible_chat"}), OpenAICompatibleChatProvider)

    def test_example_key_is_not_usable(self):
        provider = create_provider({"provider": "openai_responses", "api_key": "replace-me"})
        with self.assertRaisesRegex(RuntimeError, "settings.local.json"):
            provider.generate("Tutor", "Question")

    def test_provider_reports_connection_failures_clearly(self):
        provider = create_provider({
            "provider": "openai_compatible_chat",
            "base_url": "https://agent.example/v1",
            "api_key": "test-key",
            "model": "test-model",
        })
        with patch("urllib.request.OpenerDirector.open", side_effect=urllib.error.URLError("refused")):
            with self.assertRaisesRegex(RuntimeError, "Cannot connect to the agent API"):
                provider.generate("Tutor", "Question")

    def test_tutor_policy_contains_integrity_boundary(self):
        policy = app.TUTOR.read_text(encoding="utf-8")
        self.assertIn("Do not produce submission-ready answers", policy)

    def test_markdown_cleanup_preserves_language_operators(self):
        cleaned = clean_text("# Parsing\n`1 + 2 * 3` and `a - b`")
        self.assertIn("1 + 2 * 3", cleaned)
        self.assertIn("a - b", cleaned)

    def test_form_feed_chunks_keep_pdf_page_numbers(self):
        item = {"id": "lecture-01", "title": "Overview", "file": "lecture-01.txt",
                "display_file": "lecture01.pdf"}
        collection = {"id": "lectures", "title": "Lectures"}
        chunks = list(item_chunks(item, collection, "first page\fsecond page"))
        self.assertEqual([chunk["page"] for chunk in chunks], [1, 2])
        self.assertEqual(chunks[1]["display_file"], "lecture01.pdf")


if __name__ == "__main__":
    unittest.main()
