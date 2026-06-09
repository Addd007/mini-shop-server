from __future__ import annotations

from typing import Any, Dict

from tests.common.assertion import AssertionHelper
from tests.common.context import TestContext


class CaseRunner:
    def __init__(self, client, context: TestContext | None = None):
        self.client = client
        self.context = context or TestContext()

    def run_case(self, case: Dict[str, Any]):
        case = self.context.resolve(case)
        method = case["method"]
        url = case["url"]
        headers = case.get("headers") or {}
        request_data = case.get("request") or {}
        params = case.get("params") or None
        data = case.get("data") or None
        files = case.get("files") or None

        response = self.client.request(
            method,
            url,
            params=params,
            json=request_data if method.upper() in {"POST", "PUT", "PATCH"} else None,
            data=data,
            files=files,
            headers=headers,
        )

        expected = case.get("assert", {})
        if "status_code" in expected:
            AssertionHelper.assert_status_code(response, expected["status_code"])

        response_json = None
        try:
            response_json = response.json()
        except Exception:
            response_json = None

        if response_json is not None and "json_contains" in expected:
            AssertionHelper.assert_json_contains(response_json, expected["json_contains"])

        if "text_contains" in expected:
            AssertionHelper.assert_contains_text(response.text, expected["text_contains"])

        extract = case.get("extract") or {}
        if response_json is not None and extract:
            for key, path in extract.items():
                value = self._extract_from_json(response_json, path)
                self.context.set(key, value)

        return response

    def _extract_from_json(self, data: Any, path: str):
        current = data
        for part in path.split("."):
            if part == "$":
                continue
            if isinstance(current, list):
                current = current[int(part)]
            else:
                current = current.get(part)
        return current
