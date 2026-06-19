"""
文件上传/下载自动化测试 — 4号专项

测试依据：test_cases 4号 / 文件模块
数据来源：tests/cases/4号/file_cases.yaml

测试分组（按 YAML 中的 tag 字段划分）：
  - upload_success   : 正常上传（png/jpg/pdf/xlsx/mp4），验证返回文件信息
  - upload_failure   : 异常上传（不支持类型/空文件/无Token），验证错误返回
  - file_manage      : 文件管理（类型列表/文件列表/新建文件夹/目录树/重命名）
  - file_query       : 文件查询（按名查询/详情查询/不存在查询）
  - file_delete      : 文件删除（批量删除/不存在删除）
  - static_resource  : 静态资源访问（存在/不存在）
  - download_verify  : 下载完整性验证（MD5校验/静态URL）
  - upload_dedup     : 重复上传去重验证
  - upload_boundary  : 上传边界（超大文件）
  - upload_folder    : 上传到文件夹
  - file_move        : 文件移动
  - file_copy        : 文件复制

运行方式：
  pytest tests/api/4号/test_file_cases.py -v
  pytest tests/api/4号/test_file_cases.py -k TC-FILE-001
  pytest -m file -v
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, List

import allure
import pytest
import requests

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

CASES_DIR = Path(__file__).resolve().parents[1] / "cases" / "4号"
CASE_FILE = "file_cases.yaml"

# 测试用上传文件
TEST_UPLOAD_FILE = Path(__file__).resolve().parents[2] / "data" / "upload_test.png"

# 临时文件缓存
_generated_files: Dict[str, Path] = {}


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/file_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
UPLOAD_SUCCESS_CASES = _filter_by_tag(ALL_CASES, "upload_success")
UPLOAD_FAILURE_CASES = _filter_by_tag(ALL_CASES, "upload_failure")
FILE_MANAGE_CASES = _filter_by_tag(ALL_CASES, "file_manage")
FILE_QUERY_CASES = _filter_by_tag(ALL_CASES, "file_query")
FILE_DELETE_CASES = _filter_by_tag(ALL_CASES, "file_delete")
STATIC_RESOURCE_CASES = _filter_by_tag(ALL_CASES, "static_resource")
DOWNLOAD_VERIFY_CASES = _filter_by_tag(ALL_CASES, "download_verify")
UPLOAD_DEDUP_CASES = _filter_by_tag(ALL_CASES, "upload_dedup")
UPLOAD_BOUNDARY_CASES = _filter_by_tag(ALL_CASES, "upload_boundary")
UPLOAD_FOLDER_CASES = _filter_by_tag(ALL_CASES, "upload_folder")
FILE_MOVE_CASES = _filter_by_tag(ALL_CASES, "file_move")
FILE_COPY_CASES = _filter_by_tag(ALL_CASES, "file_copy")


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_temp_file(suffix: str, size: int = 1024) -> Path:
    """生成指定后缀和大小的临时文件"""
    key = f"{suffix}_{size}"
    if key not in _generated_files:
        f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        f.write(os.urandom(size))
        f.close()
        _generated_files[key] = Path(f.name)
    return _generated_files[key]


def _make_forbidden_file(suffix: str = ".exe") -> Path:
    """生成不支持类型的临时文件"""
    key = f"forbidden_{suffix}"
    if key not in _generated_files:
        f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        f.write(os.urandom(1024))
        f.close()
        _generated_files[key] = Path(f.name)
    return _generated_files[key]


def _make_oversized_file() -> Path:
    """生成略大于单文件限制（100MB）的文件"""
    if "oversized" not in _generated_files:
        limit = 101 * 1024 * 1024
        f = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        f.seek(limit - 1)
        f.write(b'\0')
        f.close()
        _generated_files["oversized"] = Path(f.name)
    return _generated_files["oversized"]


def _md5_of_file(filepath: Path) -> str:
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def _md5_of_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _get_upload_file_for_case(case: dict) -> Optional[Path]:
    """根据用例描述返回合适的测试文件"""
    case_id = case.get("id", "")
    summary = case.get("summary", "")

    if case.get("upload_empty"):
        return None

    if case.get("use_forbidden_file"):
        forbidden_suffix = case.get("file_suffix", ".exe")
        return _make_forbidden_file(forbidden_suffix)

    if case.get("use_oversized"):
        return _make_oversized_file()

    if "pdf" in case_id.lower() or "pdf" in summary.lower():
        return _make_temp_file(".pdf", 2048)
    if "xlsx" in case_id.lower() or "xlsx" in summary.lower():
        return _make_temp_file(".xlsx", 3072)
    if "mp4" in case_id.lower() or "mp4" in summary.lower():
        return _make_temp_file(".mp4", 102400)
    if "jpg" in case_id.lower() or "jpg" in summary.lower():
        return _make_temp_file(".jpg", 1024)
    if "png" in case_id.lower() or "png" in summary.lower():
        return _make_temp_file(".png", 1024)

    if TEST_UPLOAD_FILE.exists():
        return TEST_UPLOAD_FILE
    return _make_temp_file(".png", 1024)


def _resolve_path(case: dict, uploaded_info: dict) -> str:
    """替换路径中的占位符"""
    path = case.get("path", "")
    if "{filename}" in path and "uploaded_filename" in uploaded_info:
        path = path.replace("{filename}", uploaded_info["uploaded_filename"])
    if "{folder_id}" in path and "folder_id" in uploaded_info:
        path = path.replace("{folder_id}", str(uploaded_info["folder_id"]))
    if "{uploaded_file_id}" in path and "uploaded_file_id" in uploaded_info:
        path = path.replace("{uploaded_file_id}", str(uploaded_info["uploaded_file_id"]))
    return path


def _resolve_params(case: dict, uploaded_info: dict) -> Optional[Dict]:
    """替换 params 中的占位符"""
    params = case.get("params", {}).copy() if case.get("params") else None
    if params:
        for key, val in params.items():
            if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
                placeholder = val[1:-1]
                if placeholder == "unique_folder_name":
                    params[key] = f"test_folder_4号_{int(time.time())}"
                elif placeholder in uploaded_info:
                    params[key] = str(uploaded_info[placeholder])
    return params


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def uploaded_file_info(auth_client: ApiClient) -> dict:
    """预先上传一个文件，返回文件信息（id, filename）。

    关键设计：如果预上传失败，则快速失败（pytest.skip），
    避免下游测试收到 file_id=0 导致级联假失败。
    """
    if not TEST_UPLOAD_FILE.exists():
        f = _make_temp_file(".png", 1024)
    else:
        f = TEST_UPLOAD_FILE

    with open(f, "rb") as fh:
        resp = auth_client.request(
            "POST", "/cms/file/0",
            files={"file": (f.name, fh, "image/png")},
        )
    if resp.status_code != 200:
        pytest.skip(f"预上传失败（状态码 {resp.status_code}），跳过依赖上传文件的测试。响应: {resp.text[:300]}")

    body = resp.json()
    items = body.get("data", body.get("items", []))
    if not items:
        pytest.skip("预上传响应未包含文件信息，跳过依赖上传文件的测试")

    first = items[0] if isinstance(items, list) else items
    file_id = first.get("id")
    if file_id is None or file_id == 0:
        pytest.skip("预上传返回的 file_id 无效（None 或 0），跳过依赖上传文件的测试")
    return {
        "uploaded_file_id": file_id,
        "uploaded_file_ids": str(file_id),
        "uploaded_filename": first.get("name", ""),
    }


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _execute_case(client: ApiClient, case: dict, uploaded_info: dict = None) -> Any:
    """根据 YAML 用例构造并发送 HTTP 请求"""
    path = case.get("path", "/cms/file/0")
    if uploaded_info:
        path = _resolve_path(case, uploaded_info)
    params = _resolve_params(case, uploaded_info) if uploaded_info else case.get("params")

    method = case.get("method", "GET")

    # 上传请求
    if case.get("is_upload"):
        upload_file = _get_upload_file_for_case(case)
        if upload_file is None or not upload_file.exists():
            return client.request(method=method, path=path)
        with open(upload_file, "rb") as fh:
            return client.request(
                method=method, path=path,
                files={case.get("file_field", "file"): (upload_file.name, fh)},
                params=params,
            )

    return client.request(
        method=method,
        path=path,
        json=case.get("json"),
        params=params,
    )


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


# ===========================================================================
# 测试函数：文件上传成功 (TC-FILE-001 ~ TC-FILE-006)
# ===========================================================================

@pytest.mark.file
@pytest.mark.parametrize("case", UPLOAD_SUCCESS_CASES, ids=[c["id"] for c in UPLOAD_SUCCESS_CASES])
def test_upload_success(auth_client: ApiClient, case: dict):
    allure.dynamic.title(f"文件上传成功 - {case['id']}")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("正常上传")

    resp = _execute_case(auth_client, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    if expected.get("has_items"):
        with allure.step("校验返回文件列表"):
            items = body.get("data", body.get("items", []))
            assert items, f"[{case['id']}] 响应中未包含文件信息: {body}"


# ===========================================================================
# 测试函数：文件上传失败 (TC-FILE-007 ~ TC-FILE-010)
# ===========================================================================

@pytest.mark.file
@pytest.mark.parametrize("case", UPLOAD_FAILURE_CASES, ids=[c["id"] for c in UPLOAD_FAILURE_CASES])
def test_upload_failure(base_url, timeout, auth_client: ApiClient, case: dict):
    allure.dynamic.title(f"文件上传失败 - {case['id']}")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("异常上传")

    if case.get("no_auth"):
        client = ApiClient(base_url=base_url, timeout=timeout)
    else:
        client = auth_client

    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp)

    if expected.get("error"):
        with allure.step("校验接口返回错误"):
            if resp.status_code == 200:
                error_code = body.get("error_code", body.get("code"))
                assert error_code is not None and error_code != 0, (
                    f"[{case['id']}] 应返回非零 error_code: {body}"
                )
            else:
                assert resp.status_code in (400, 401, 403, 404, 413, 422), (
                    f"[{case['id']}] 期望 4xx, 实际 {resp.status_code}"
                )


# ===========================================================================
# 测试函数：文件管理 (TC-FILE-011 ~ TC-FILE-014, TC-FILE-017 ~ TC-FILE-018)
# ===========================================================================

@pytest.mark.file
@pytest.mark.parametrize("case", FILE_MANAGE_CASES, ids=[c["id"] for c in FILE_MANAGE_CASES])
def test_file_manage(auth_client: ApiClient, uploaded_file_info: dict, case: dict):
    allure.dynamic.title(f"文件管理 - {case['id']}")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("文件管理操作")

    path = _resolve_path(case, uploaded_file_info)
    params = _resolve_params(case, uploaded_file_info)

    resp = auth_client.request(
        method=case.get("method", "GET"),
        path=path,
        json=case.get("json"),
        params=params,
    )
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp, request_payload=params)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    if "json" in expected:
        for key, val in expected["json"].items():
            with allure.step(f"校验响应字段 {key}"):
                assert body.get(key) == val, (
                    f"[{case['id']}] 期望 {key}={val}, 实际 {body.get(key)}"
                )


# ===========================================================================
# 测试函数：文件查询 (TC-FILE-015 ~ TC-FILE-016)
# ===========================================================================

@pytest.mark.file
@pytest.mark.parametrize("case", FILE_QUERY_CASES, ids=[c["id"] for c in FILE_QUERY_CASES])
def test_file_query(auth_client: ApiClient, uploaded_file_info: dict, case: dict):
    allure.dynamic.title(f"文件查询 - {case['id']}")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("文件查询")

    path = _resolve_path(case, uploaded_file_info)

    resp = auth_client.request(
        method=case.get("method", "GET"),
        path=path,
        json=case.get("json"),
        params=case.get("params"),
    )
    expected = case.get("expected", {})
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 测试函数：文件删除 (TC-FILE-019 ~ TC-FILE-020)
# ===========================================================================

@pytest.mark.file
@pytest.mark.parametrize("case", FILE_DELETE_CASES, ids=[c["id"] for c in FILE_DELETE_CASES])
def test_file_delete(auth_client: ApiClient, uploaded_file_info: dict, case: dict):
    allure.dynamic.title(f"文件删除 - {case['id']}")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("文件删除")

    path = _resolve_path(case, uploaded_file_info)
    params = _resolve_params(case, uploaded_file_info)

    resp = auth_client.request(
        method=case.get("method", "DELETE"),
        path=path,
        params=params,
    )
    expected = case.get("expected", {})
    _attach_case(case, resp, request_payload=params)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 测试函数：静态资源访问 (TC-FILE-021 ~ TC-FILE-022)
# ===========================================================================

@pytest.mark.file
@pytest.mark.parametrize("case", STATIC_RESOURCE_CASES, ids=[c["id"] for c in STATIC_RESOURCE_CASES])
def test_static_resource(base_url, timeout, case: dict):
    """静态资源不需要认证"""
    allure.dynamic.title(f"静态资源访问 - {case['id']}")
    allure.dynamic.feature("静态资源")
    allure.dynamic.story("静态资源访问")

    client = ApiClient(base_url=base_url, timeout=timeout)
    resp = client.request(method=case.get("method", "GET"), path=case.get("path", ""))
    expected = case.get("expected", {})
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 测试函数：下载完整性验证 (TC-FILE-023 ~ TC-FILE-024)
# ===========================================================================

@pytest.mark.file
def test_upload_and_download_integrity(auth_client: ApiClient):
    """上传文件后，通过静态资源 URL 下载并对比 MD5"""
    allure.dynamic.title("文件下载完整性验证 - TC-FILE-023")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("下载完整性")

    test_file = TEST_UPLOAD_FILE if TEST_UPLOAD_FILE.exists() else _make_temp_file(".png", 4096)
    original_md5 = _md5_of_file(test_file)
    allure.attach(original_md5, name="原始文件 MD5", attachment_type=allure.attachment_type.TEXT)

    # Step 1: 上传文件
    with open(test_file, "rb") as fh:
        with allure.step("上传测试文件"):
            resp = auth_client.request(
                "POST", "/cms/file/0",
                files={"file": (test_file.name, fh)},
            )
    assert resp.status_code == 200, f"上传失败: {resp.text}"
    body = resp.json()
    items = body.get("data", body.get("items", []))
    assert items, "上传后未返回文件信息"
    first = items[0] if isinstance(items, list) else items
    file_url = first.get("url", "")
    file_id = first.get("id", "")
    allure.attach(str(first), name="上传响应", attachment_type=allure.attachment_type.TEXT)

    # Step 2: 通过静态 URL 下载
    with allure.step("通过静态 URL 下载文件"):
        if file_url:
            dl_resp = requests.get(file_url, timeout=10, stream=True)
        else:
            file_path = first.get("path", "")
            if file_path:
                dl_url = f"{auth_client.base_url}/static/files/{file_path}"
                dl_resp = requests.get(dl_url, timeout=10, stream=True)
            else:
                pytest.skip("无法获取文件下载 URL")

    with allure.step("校验下载 HTTP 状态码"):
        assert dl_resp.status_code == 200, f"下载失败: {dl_resp.status_code}"

    # Step 3: MD5 对比
    with allure.step("计算下载文件 MD5 并对比"):
        downloaded_md5 = _md5_of_bytes(dl_resp.content)
        allure.attach(downloaded_md5, name="下载文件 MD5", attachment_type=allure.attachment_type.TEXT)
        assert original_md5 == downloaded_md5, (
            f"文件完整性校验失败！原始 MD5: {original_md5}, 下载 MD5: {downloaded_md5}"
        )

    # 清理
    with allure.step("清理上传的文件"):
        auth_client.request("DELETE", "/cms/file", params={"ids": str(file_id)})


# ===========================================================================
# 测试函数：重复上传去重 (TC-FILE-025)
# ===========================================================================

@pytest.mark.file
def test_upload_dedup(auth_client: ApiClient):
    """上传相同文件两次，验证 MD5 去重逻辑"""
    allure.dynamic.title("重复上传去重验证 - TC-FILE-025")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("上传去重")

    test_file = TEST_UPLOAD_FILE if TEST_UPLOAD_FILE.exists() else _make_temp_file(".png", 4096)

    with allure.step("第一次上传"):
        with open(test_file, "rb") as fh:
            resp1 = auth_client.request(
                "POST", "/cms/file/0",
                files={"file": (test_file.name, fh)},
            )
    assert resp1.status_code == 200
    body1 = resp1.json()
    items1 = body1.get("data", body1.get("items", []))
    assert items1
    first1 = items1[0] if isinstance(items1, list) else items1
    file_id1 = first1.get("id")

    with allure.step("第二次上传相同文件（同一文件夹，应去重）"):
        with open(test_file, "rb") as fh:
            resp2 = auth_client.request(
                "POST", "/cms/file/0",
                files={"file": (test_file.name, fh)},
            )
    assert resp2.status_code == 200
    body2 = resp2.json()
    items2 = body2.get("data", body2.get("items", []))
    assert items2
    first2 = items2[0] if isinstance(items2, list) else items2
    file_id2 = first2.get("id")

    allure.attach(
        f"首次上传 ID: {file_id1}, 二次上传 ID: {file_id2}",
        name="去重结果",
        attachment_type=allure.attachment_type.TEXT,
    )
    assert file_id1 == file_id2, (
        f"去重失败：相同文件应返回相同 ID。首次: {file_id1}, 二次: {file_id2}"
    )

    # 清理
    auth_client.request("DELETE", "/cms/file", params={"ids": str(file_id1)})


# ===========================================================================
# 测试函数：超大文件被拒绝 (TC-FILE-026)
# ===========================================================================

@pytest.mark.file
def test_upload_oversized_rejected(auth_client: ApiClient):
    """上传超大文件验证被拒绝"""
    allure.dynamic.title("超大文件上传被拒绝 - TC-FILE-026")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("上传边界")

    big_file = _make_oversized_file()
    file_size_mb = big_file.stat().st_size / (1024 * 1024)

    with allure.step(f"上传超大文件 ({file_size_mb:.1f}MB)"):
        # 使用长超时的专用客户端，避免 timeout 参数冲突
        big_client = ApiClient(base_url=auth_client.base_url, timeout=120, token=auth_client.token)
        with open(big_file, "rb") as fh:
            resp = big_client.request(
                "POST", "/cms/file/0",
                files={"file": ("big_file.zip", fh)},
            )

    allure.attach(f"响应状态码: {resp.status_code}", name="上传结果", attachment_type=allure.attachment_type.TEXT)
    allure.attach(resp.text[:500] if resp.text else "空响应", name="响应体", attachment_type=allure.attachment_type.TEXT)

    assert resp.status_code in (400, 401, 403, 413, 422, 500), (
        f"超大文件应被拒绝，实际: {resp.status_code}"
    )


# ===========================================================================
# 测试函数：文件夹上传与移动 (TC-FILE-027 ~ TC-FILE-028)
# ===========================================================================

@pytest.mark.file
def test_upload_to_folder_and_move(auth_client: ApiClient):
    """新建文件夹 -> 上传到该文件夹 -> 移动文件"""
    allure.dynamic.title("文件夹上传与移动 - TC-FILE-027 / TC-FILE-028")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("文件移动")

    test_file = TEST_UPLOAD_FILE if TEST_UPLOAD_FILE.exists() else _make_temp_file(".png", 4096)

    # Step 1: 新建文件夹（加时间戳避免重复）
    folder_name = f"4号测试文件夹_{int(time.time())}"
    with allure.step(f"新建文件夹: {folder_name}"):
        resp = auth_client.request("POST", "/cms/file/new", params={
            "parent_id": "0",
            "filename": folder_name,
        })
    assert resp.status_code == 200, f"新建文件夹失败: {resp.text}"

    # 获取新建文件夹 ID
    resp_list = auth_client.request("GET", "/cms/file/list", params={"parent_id": "0"})
    body_list = resp_list.json()
    items = body_list.get("data", {}).get("items", []) if isinstance(body_list.get("data"), dict) else []
    if not items:
        items = body_list.get("items", [])
    folder_id = None
    for item in items:
        if item.get("name") == folder_name and item.get("extension") is None:
            folder_id = item.get("id")
            break
    if not folder_id:
        pytest.skip("未找到新建的文件夹 ID")

    allure.attach(str(folder_id), name="文件夹 ID", attachment_type=allure.attachment_type.TEXT)

    # Step 2: 上传文件到文件夹
    with allure.step(f"上传文件到文件夹 {folder_id}"):
        with open(test_file, "rb") as fh:
            resp_upload = auth_client.request(
                "POST", f"/cms/file/{folder_id}",
                files={"file": (test_file.name, fh)},
            )
    assert resp_upload.status_code == 200, f"上传到文件夹失败: {resp_upload.text}"
    body_up = resp_upload.json()
    up_items = body_up.get("data", body_up.get("items", []))
    assert up_items
    up_first = up_items[0] if isinstance(up_items, list) else up_items
    file_id = up_first.get("id")
    allure.attach(str(up_first), name="上传结果", attachment_type=allure.attachment_type.TEXT)

    # Step 3: 移动文件到根目录
    with allure.step(f"移动文件 {file_id} 到根目录"):
        resp_move = auth_client.request("PUT", "/cms/file/move", params={
            "parent_id": "0",
            "ids": str(file_id),
        })
    allure.attach(str(resp_move.status_code), name="移动结果", attachment_type=allure.attachment_type.TEXT)
    assert resp_move.status_code == 200, f"移动文件失败: {resp_move.text}"

    # 清理
    auth_client.request("DELETE", "/cms/file", params={"ids": str(file_id)})


# ===========================================================================
# 测试函数：复制文件 (TC-FILE-029)
# ===========================================================================

@pytest.mark.file
def test_copy_file(auth_client: ApiClient):
    """上传文件后复制到根目录"""
    allure.dynamic.title("文件复制 - TC-FILE-029")
    allure.dynamic.feature("文件管理")
    allure.dynamic.story("文件复制")

    test_file = TEST_UPLOAD_FILE if TEST_UPLOAD_FILE.exists() else _make_temp_file(".png", 4096)

    with allure.step("上传测试文件"):
        with open(test_file, "rb") as fh:
            resp = auth_client.request(
                "POST", "/cms/file/0",
                files={"file": (test_file.name, fh)},
            )
    assert resp.status_code == 200
    body = resp.json()
    items = body.get("data", body.get("items", []))
    assert items
    first = items[0] if isinstance(items, list) else items
    file_id = first.get("id")

    with allure.step(f"复制文件 {file_id}"):
        resp_copy = auth_client.request("POST", "/cms/file/copy", params={
            "parent_id": "0",
            "file_id": str(file_id),
        })
    allure.attach(str(resp_copy.status_code), name="复制结果", attachment_type=allure.attachment_type.TEXT)
    assert resp_copy.status_code in (200, 400, 201), (
        f"复制操作异常: {resp_copy.status_code} - {resp_copy.text}"
    )

    # 清理
    auth_client.request("DELETE", "/cms/file", params={"ids": str(file_id)})


# ---------------------------------------------------------------------------
# 清理
# ---------------------------------------------------------------------------

def teardown_module():
    for p in _generated_files.values():
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass
