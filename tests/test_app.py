import json
import os
import unittest
from pathlib import Path

os.environ["COURSEWEAVER_CONFIG"] = str(
    Path(__file__).resolve().parent.parent / "config" / "settings.example.json"
)

import app
from providers import OpenAICompatibleChatProvider, OpenAIResponsesProvider, create_provider
from scripts.build_index import clean_text


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

    def test_provider_selection(self):
        self.assertIsInstance(create_provider({"provider": "openai_responses"}), OpenAIResponsesProvider)
        self.assertIsInstance(create_provider({"provider": "openai_compatible_chat"}), OpenAICompatibleChatProvider)

    def test_example_key_is_not_usable(self):
        provider = create_provider({"provider": "openai_responses", "api_key": "replace-me"})
        with self.assertRaisesRegex(RuntimeError, "settings.local.json"):
            provider.generate("Tutor", "Question")

    def test_tutor_policy_contains_integrity_boundary(self):
        policy = app.TUTOR.read_text(encoding="utf-8")
        self.assertIn("Do not produce submission-ready answers", policy)

    def test_markdown_cleanup_preserves_language_operators(self):
        cleaned = clean_text("# Parsing\n`1 + 2 * 3` and `a - b`")
        self.assertIn("1 + 2 * 3", cleaned)
        self.assertIn("a - b", cleaned)


if __name__ == "__main__":
    unittest.main()
