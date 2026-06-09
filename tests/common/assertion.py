from __future__ import annotations

from typing import Any, Dict


class AssertionErrorDetail(AssertionError):
    pass


class AssertionHelper:
    @staticmethod
    def assert_status_code(response: Any, expected: int) -> None:
        actual = getattr(response, "status_code", None)
        if actual != expected:
            raise AssertionErrorDetail(f"Expected status code {expected}, got {actual}")

    @staticmethod
    def assert_json_contains(response_json: Dict[str, Any], expected: Dict[str, Any]) -> None:
        for key, value in expected.items():
            if key not in response_json:
                raise AssertionErrorDetail(f"Missing key '{key}' in response JSON")
            if response_json[key] != value:
                raise AssertionErrorDetail(
                    f"Key '{key}' expected value {value!r}, got {response_json[key]!r}"
                )

    @staticmethod
    def assert_contains_text(response_text: str, expected_text: str) -> None:
        if expected_text not in response_text:
            raise AssertionErrorDetail(f"Response text does not contain '{expected_text}'")
