from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest
 

class _DummyFile:
    """模拟上传文件对象，只记录 filename 和 save 调用参数。"""

    def __init__(self, filename: str):
        self.filename = filename
        self.saved_path = None

    def save(self, path: str):
        self.saved_path = path


@pytest.fixture()
def file_mod(monkeypatch):
    """直接加载 `app/service/file.py`，避免触发项目包初始化依赖。"""
    module_path = Path(__file__).resolve().parents[2] / "app" / "service" / "file.py"
    spec = spec_from_file_location("tests.unit.file_service_module", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "current_app", SimpleNamespace(config={"UPLOAD_FOLDER": "/tmp/uploads"}))
    return module


def test_save_uses_file_filename_and_default_upload_folder(file_mod):
    """不显式传入文件名和保存目录时，应使用文件自身名称和应用默认上传目录。"""
    file = _DummyFile("avatar.png")
    service = file_mod.FileService(file)

    result = service.save()

    assert result == "avatar.png"
    assert file.saved_path == "/tmp/uploads/avatar.png"
    assert service.prefix_path == "/tmp/uploads"
    assert service.file is file


def test_save_prefers_explicit_filename_and_prefix_path(file_mod):
    """显式传入 filename 与 prefix_path 时，应优先使用调用参数。"""
    file = _DummyFile("avatar.png")
    service = file_mod.FileService(file)

    result = service.save(filename="profile.jpg", prefix_path="/data/files")

    assert result == "profile.jpg"
    assert file.saved_path == "/data/files/profile.jpg"


def test_save_uses_default_prefix_path_when_only_filename_is_explicit(file_mod):
    """只传 filename 时，应保留默认上传目录不变。"""
    file = _DummyFile("avatar.png")
    service = file_mod.FileService(file)

    result = service.save(filename="custom.png")

    assert result == "custom.png"
    assert file.saved_path == "/tmp/uploads/custom.png"


def test_save_falls_back_to_file_name_when_filename_is_empty(file_mod):
    """当 filename 传空字符串时，应回退到文件自身的 filename。"""
    file = _DummyFile("fallback.png")
    service = file_mod.FileService(file)

    result = service.save(filename="")

    assert result == "fallback.png"
    assert file.saved_path == "/tmp/uploads/fallback.png"


def test_save_uses_default_prefix_path_when_prefix_path_is_empty(file_mod):
    """当 prefix_path 传空字符串时，应回退到应用默认上传目录。"""
    file = _DummyFile("cover.jpg")
    service = file_mod.FileService(file)

    result = service.save(prefix_path="")

    assert result == "cover.jpg"
    assert file.saved_path == "/tmp/uploads/cover.jpg"


class _NoSaveFile:
    """缺少 save 方法的文件对象。"""

    def __init__(self, filename: str):
        self.filename = filename


class _BrokenSaveFile:
    """save 方法会主动抛错的文件对象。"""

    def __init__(self, filename: str):
        self.filename = filename
        self.saved_path = None

    def save(self, path: str):
        self.saved_path = path
        raise OSError("disk full")


def test_save_raises_attribute_error_when_file_is_none(file_mod):
    """当 file 为 None 时，初始化后保存应抛出属性错误。"""
    service = file_mod.FileService(None)

    with pytest.raises(AttributeError):
        service.save()


def test_save_raises_attribute_error_when_file_has_no_save_method(file_mod):
    """当文件对象缺少 save 方法时，应抛出属性错误。"""
    service = file_mod.FileService(_NoSaveFile("no_save.png"))

    with pytest.raises(AttributeError):
        service.save()


def test_save_raises_type_error_when_file_name_is_none(file_mod):
    """当文件名为 None 时，路径拼接应抛出类型错误。"""
    file = _DummyFile("ignored.png")
    file.filename = None
    service = file_mod.FileService(file)

    with pytest.raises(TypeError):
        service.save()


def test_save_propagates_os_error_from_file_save(file_mod):
    """当底层 save 失败时，异常应直接向上抛出。"""
    service = file_mod.FileService(_BrokenSaveFile("broken.png"))

    with pytest.raises(OSError, match="disk full"):
        service.save()
