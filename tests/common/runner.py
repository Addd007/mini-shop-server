from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from tests.common.api_client import ApiClient
from tests.common.assertion import AssertionHelper


@dataclass
class CaseResult:
    case_id: str
    success: bool
    status_code: Optional[int] = None
    response_json: Optional[Dict[str, Any]] = None
    response_text: Optional[str] = None
    error: Optional[str] = None


class YamlCaseRunner:
    def __init__(self, client: ApiClient):
        self.client = client

    def run_case(self, case: Dict[str, Any]) -> CaseResult:
        case_id = str(case.get("id", ""))
        method = str(case.get("method", "GET"))
        path = str(case.get("path", ""))
        headers = case.get("headers") or {}
        params = case.get("params")
        json_body = case.get("json")
        data = case.get("data")
        files = case.get("files")
        expected = case.get("expected") or {}

        try:
            response = self.client.request(
                method,
                path,
                params=params,
                json=json_body,
                data=data,
                files=files,
                headers=headers,
            )

            AssertionHelper.assert_status_code(
                response,
                int(expected.get("status_code", 200)),
            )

            response_json: Optional[Dict[str, Any]] = None
            response_text: Optional[str] = None
            try:
                response_json = response.json()
            except Exception:
                response_text = getattr(response, "text", None)

            expected_json = expected.get("json")
            if expected_json is not None:
                if response_json is None:
                    raise AssertionError("Expected JSON response, but response is not JSON")
                AssertionHelper.assert_json_contains(response_json, expected_json)

            expected_text = expected.get("text")
            if expected_text is not None:
                if response_text is None:
                    response_text = getattr(response, "text", "")
                AssertionHelper.assert_contains_text(response_text, str(expected_text))

            return CaseResult(
                case_id=case_id,
                success=True,
                status_code=getattr(response, "status_code", None),
                response_json=response_json,
                response_text=response_text,
            )
        except Exception as exc:
            return CaseResult(
                case_id=case_id,
                success=False,
                error=str(exc),
            )

    def run_cases(self, cases: Iterable[Dict[str, Any]]) -> List[CaseResult]:
        return [self.run_case(case) for case in cases]
