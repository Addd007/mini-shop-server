from __future__ import annotations

import json
from typing import Any, Optional

import allure


def attach_json(name: str, payload: Any) -> None:
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def attach_text(name: str, payload: Any) -> None:
    allure.attach(
        str(payload),
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )


def attach_request_response(payload: Any, response: Any, *, request_name: str = "请求数据", response_name: str = "响应数据") -> None:
    attach_json(request_name, payload)
    attach_text(response_name, getattr(response, "text", response))


def set_case_title(prefix: str, case_id: str, extra: Optional[str] = None) -> None:
    title = f"{prefix} - {case_id}"
    if extra:
        title = f"{title} - {extra}"
    allure.dynamic.title(title)
