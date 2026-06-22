from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.service.file import FileService


class _DummyFile:
    """模拟上传文件对象，只记录 filename 和 save 调用参数。"""

    def __init__(self, filename: str):
        self.filename = filename
        self.saved_path = None

    def save(self, path: str):
        self.saved_path = path


@pytest.fixture()
def app_ctx(monkeypatch):
    """给 `FileService` 提供一个最小可用的 `current_app.config`。"""
    import app.service.file as file_mod

    monkeypatch.setattr(file_mod, "current_app", SimpleNamespace(config={"UPLOAD_FOLDER": "/tmp/uploads"}))
    return file_mod


def test_save_uses_file_filename_and_default_upload_folder(app_ctx):
    """不显式传入文件名和保存目录时，应使用文件自身名称和应用默认上传目录。"""
    file = _DummyFile("avatar.png")
    service = FileService(file)

    result = service.save()

    assert result == "avatar.png"
    assert file.saved_path == "/tmp/uploads/avatar.png"
    assert service.prefix_path == "/tmp/uploads"
    assert service.file is file


def test_save_prefers_explicit_filename_and_prefix_path(app_ctx):
    """显式传入 filename 与 prefix_path 时，应优先使用调用参数。"""
    file = _DummyFile("avatar.png")
    service = FileService(file)

    result = service.save(filename="profile.jpg", prefix_path="/data/files")

    assert result == "profile.jpg"
    assert file.saved_path == "/data/files/profile.jpg"


def test_save_uses_default_prefix_path_when_only_filename_is_explicit(app_ctx):
    """只传 filename 时，应保留默认上传目录不变。"""
    file = _DummyFile("avatar.png")
    service = FileService(file)

    result = service.save(filename="custom.png")

    assert result == "custom.png"
    assert file.saved_path == "/tmp/uploads/custom.png"


def test_save_falls_back_to_file_name_when_filename_is_empty(app_ctx):
    """当 filename 传空字符串时，应回退到文件自身的 filename。"""
    file = _DummyFile("fallback.png")
    service = FileService(file)

    result = service.save(filename="")

    assert result == "fallback.png"
    assert file.saved_path == "/tmp/uploads/fallback.png"
