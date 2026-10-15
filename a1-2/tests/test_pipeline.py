"""외부 API를 호출하지 않고 요구사항의 성공/실패 분기를 점검합니다."""

import argparse
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import package_submission as package
import travel_planner as app


REC = {"recommended_city": "강릉", "weather": "가을 날씨 (예보 아님)",
       "events": ["지역행사 후보 (개최 미확인)"], "reason": "산책하기 좋은 계절입니다. 바다를 볼 수 있습니다."}
PLACE = {"documents": [{"place_name": "테스트 식당", "road_address_name": "강원특별자치도 강릉시 테스트로 1",
                        "category_name": "음식점 > 한식", "place_url": "https://place.map.kakao.com/123",
                        "x": "128.9", "y": "37.7"}]}
ENV = {"GEMINI_API_KEY": "test-gemini-secret-value", "KAKAO_REST_API_KEY": "test-kakao-secret-value"}


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, ENV, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()
        self.addCleanup(self.quiet.__exit__, None, None, None)

    def test_calendar_validation(self):
        self.assertEqual(app.valid_date("2028-02-29"), "2028-02-29")
        for value in ("2026-02-29", "2026-13-01", "2026-1-01", "20XX-03-15"):
            with self.assertRaises(argparse.ArgumentTypeError):
                app.valid_date(value)

    def test_date_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            app.main([])
        self.assertEqual(error.exception.code, 2)

    def test_missing_keys_stop_before_network(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(app, "load_env"), \
                patch.object(app, "request_json") as request, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main(["-date", "2026-10-20"]), 1)
            request.assert_not_called()

    def test_recommendation_json_retry_then_success(self):
        errors, raw = [], {}
        with patch.object(app, "gemini_text", side_effect=[("not JSON", {}), (json.dumps(REC), {})]) as llm:
            self.assertEqual(app.recommend("2026-10-20", errors, raw), REC)
        self.assertEqual(llm.call_count, 2)
        self.assertEqual(errors[0]["type"], "JSON_PARSE_ERROR")

    def test_invalid_types_stop_after_one_retry(self):
        errors, raw = [], {}
        invalid = dict(REC, events="행사")
        with patch.object(app, "gemini_text", return_value=(json.dumps(invalid), {})) as llm:
            with self.assertRaises(app.APIError):
                app.recommend("2026-10-20", errors, raw)
        self.assertEqual(llm.call_count, 2)
        self.assertEqual(len(errors), 2)

    def test_place_failure_and_zero_are_nonfatal(self):
        for result in (app.APIError("AUTH_ERROR", "HTTP 401"), app.APIError("QUOTA_ERROR", "HTTP 429"),
                       app.APIError("NETWORK_ERROR", "연결 실패"), {"documents": []}, {"documents": None}):
            errors, raw = [], {}
            kwargs = {"side_effect": result} if isinstance(result, Exception) else {"return_value": result}
            with patch.object(app, "request_json", **kwargs):
                self.assertEqual(app.search_restaurants("강릉", errors, raw), [])
            self.assertEqual(errors[0]["step"], "place_search")

    def test_places_include_numeric_coordinates_and_source(self):
        raw = {}
        with patch.object(app, "request_json", return_value=PLACE):
            places = app.search_restaurants("강릉", [], raw)
        self.assertIsInstance(places[0]["x"], float)
        self.assertEqual(places[0]["address"], PLACE["documents"][0]["road_address_name"])
        self.assertEqual(raw["place_search"], PLACE)

    def test_http_errors_never_echo_response_body_or_key(self):
        for status, kind in ((401, "AUTH_ERROR"), (403, "AUTH_ERROR"), (429, "QUOTA_ERROR"), (500, "HTTP_ERROR")):
            exception = HTTPError("https://example.com", status, ENV["GEMINI_API_KEY"], {}, None)
            with patch.object(app, "urlopen", side_effect=exception), self.assertRaises(app.APIError) as error:
                app.request_json("https://example.com", {})
            self.assertEqual(error.exception.kind, kind)
            self.assertNotIn(ENV["GEMINI_API_KEY"], str(error.exception))
        with patch.object(app, "urlopen", side_effect=URLError("offline")), self.assertRaises(app.APIError) as error:
            app.request_json("https://example.com", {})
        self.assertEqual(error.exception.kind, "NETWORK_ERROR")

    def test_live_end_to_end_with_mocked_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            places = [{"name": "테스트 식당", "address": "테스트 주소", "category": "한식", "url": "", "x": 128.9, "y": 37.7}]
            report = app.template_report("2026-10-20", REC, places)
            with patch.object(app, "load_env"), \
                    patch.object(app, "gemini_text", side_effect=[(json.dumps(REC), {}), (report, {})]), \
                    patch.object(app, "search_restaurants", return_value=places):
                self.assertEqual(app.main(["--date", "2026-10-20", "--output-dir", tmp]), 0)
            record = json.loads(next(Path(tmp).glob("*_raw.json")).read_text())
            text = next(Path(tmp).glob("*.md")).read_text()
            self.assertEqual(record["mode"], "live")
            self.assertEqual(record["report_source"], "gemini")
            self.assertEqual(record["status"], "completed")
            self.assertIn("## 오류 요약 (errors)", text)
            self.assertIsNotNone(package.completed_run(Path(tmp)))

    def test_map_auth_failure_still_generates_report(self):
        report = app.template_report("2026-10-20", REC, [])
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, "load_env"), \
                patch.object(app, "gemini_text", side_effect=[(json.dumps(REC), {}), (report, {})]), \
                patch.object(app, "request_json", side_effect=app.APIError("AUTH_ERROR", "HTTP 401")):
            self.assertEqual(app.main(["--date", "2026-10-20", "--output-dir", tmp]), 0)
            record = json.loads(next(Path(tmp).glob("*_raw.json")).read_text())
            text = next(Path(tmp).glob("*.md")).read_text()
            self.assertEqual(record["restaurants"], [])
            self.assertEqual(record["errors"][0]["type"], "AUTH_ERROR")
            self.assertIn("데이터 없음", text)

    def test_report_failure_is_marked_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, "load_env"), \
                patch.object(app, "gemini_text", side_effect=[(json.dumps(REC), {}), app.APIError("QUOTA_ERROR", "HTTP 429")]), \
                patch.object(app, "search_restaurants", return_value=[]), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main(["--date", "2026-10-20", "--output-dir", tmp]), 1)
            record = json.loads(next(Path(tmp).glob("*_raw.json")).read_text())
            self.assertEqual(record["status"], "incomplete")
            self.assertIn("임시 보고서", next(Path(tmp).glob("*.md")).read_text())
            self.assertIsNone(package.completed_run(Path(tmp)))

    def test_demo_separate_and_rejected_for_submission(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, "load_env"), patch.object(app, "request_json") as request:
            self.assertEqual(app.main(["--date", "2026-10-20", "--demo", "--output-dir", tmp]), 0)
            request.assert_not_called()
            self.assertIsNone(package.completed_run(Path(tmp)))
            self.assertIn("연습용 데모", next(Path(tmp).glob("*.md")).read_text())

    def test_credentials_redacted_from_saved_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = {"travel_date": "2026-10-20", "reflected": ENV["GEMINI_API_KEY"], "errors": []}
            app.save_results(Path(tmp), record, ENV["KAKAO_REST_API_KEY"])
            for path in Path(tmp).iterdir():
                for secret in ENV.values():
                    self.assertNotIn(secret, path.read_text())
            json.loads(next(Path(tmp).glob("*.json")).read_text())

    def test_report_rejects_headings_without_content(self):
        empty = "\n\n".join(f"## {heading}" for heading in app.HEADINGS)
        self.assertFalse(app.valid_report(empty, REC, []))
        valid = app.template_report("2026-11-01", REC, [])
        self.assertTrue(app.valid_report(valid, REC, []))
        # 본문에 제목을 단순히 언급하는 것만으로는 필수 섹션으로 인정하지 않습니다.
        self.assertFalse(app.valid_report(valid.replace("## 날씨 요약", "날씨 요약"), REC, []))

    def test_report_requires_provided_place_url_and_category(self):
        places = [{"name": "검증 식당", "address": "검증 주소", "category": "한식 > 두부",
                   "url": "https://place.map.kakao.com/123"}]
        valid = app.template_report("2026-11-01", REC, places)
        self.assertTrue(app.valid_report(valid, REC, places))
        for field in ("name", "address", "category", "url"):
            self.assertFalse(app.valid_report(valid.replace(places[0][field], "누락"), REC, places))

    def test_report_checks_content_in_the_correct_section(self):
        valid = app.template_report("2026-11-01", REC, [])
        # 일정이 다른 섹션에만 있거나, 지역이 추천 이유에만 있으면 검증 실패입니다.
        self.assertFalse(app.valid_report(valid.replace("## 1일 일정 제안", "## 다른 내용"), REC, []))
        self.assertFalse(app.valid_report(valid.replace("## 추천 지역\n강릉", "## 추천 지역\n도시 누락"), REC, []))


if __name__ == "__main__":
    unittest.main()
