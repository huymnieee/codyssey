"""입력 검증과 실제 API 실패를 재현하는 자동 점검. 외부 API 비용 없음."""
import io
import json
import os
import socket
import unittest
import urllib.error
from unittest.mock import patch
from api.learn import ServiceError, generate_lesson, validate_input, validate_result


class ApiTests(unittest.TestCase):
    def assert_error(self, status, fn, *args):
        with self.assertRaises(ServiceError) as ctx:
            fn(*args)
        self.assertEqual(ctx.exception.status, status)

    def test_empty_short_long_input(self):
        for topic in ("", " ", "가", "가" * 501, None, 3):
            with self.subTest(topic_type=type(topic).__name__):
                self.assert_error(400, validate_input, {"topic": topic})

    def test_normal_and_200_character_input(self):
        self.assertEqual(validate_input({"topic": " API ", "level": "first"}), ("API", "first"))
        self.assertEqual(len(validate_input({"topic": "가" * 250})[0]), 250)

    def test_bad_level_or_body(self):
        for data in ([], None, {"topic": "API", "level": []}, {"topic": "API", "level": "wrong"}):
            self.assert_error(400, validate_input, data)

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_missing_key(self):
        self.assert_error(503, generate_lesson, "API", "first")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-3.1-flash-lite"})
    def test_provider_http_errors_hide_details(self):
        for provider_status, expected in ((401, 503), (403, 503), (429, 429), (500, 502)):
            err = urllib.error.HTTPError("https://example.invalid", provider_status, "private-details", {}, None)
            with patch("urllib.request.urlopen", side_effect=err):
                self.assert_error(expected, generate_lesson, "API", "first")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    def test_timeout_and_network(self):
        for err, status in ((socket.timeout(), 504), (urllib.error.URLError("offline"), 502)):
            with patch("urllib.request.urlopen", side_effect=err):
                self.assert_error(status, generate_lesson, "API", "first")

    def test_invalid_ai_result(self):
        for value in (None, [], {}, {"title": "API"}):
            with self.assertRaises(ValueError):
                validate_result(value)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-3.1-flash-lite"})
    def test_valid_provider_response_and_no_key_in_result(self):
        result = {"title": "API", "summary": "요약", "explanation": "설명 test-key", "analogy": "비유", "points": ["하나", "둘", "셋"], "quiz": {"question": "문제", "answer": "정답"}}
        raw = {"candidates": [{"content": {"parts": [{"text": json.dumps(result)}]}}]}
        stream = io.BytesIO(json.dumps(raw).encode())
        with patch("urllib.request.urlopen", return_value=stream) as call:
            output = generate_lesson("API", "first")
        self.assertEqual(output["mode"], "live")
        self.assertNotIn("test-key", json.dumps(output))
        self.assertEqual(call.call_args.kwargs["timeout"], 35)


if __name__ == "__main__":
    unittest.main()
