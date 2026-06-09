import os
from pathlib import Path

import pytest
import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "test.yaml"


@pytest.fixture(scope="session")
def test_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def base_url(test_config):
    return test_config["base_url"].rstrip("/")


@pytest.fixture(scope="session")
def test_user(test_config):
    return {
        "username": test_config["username"],
        "password": test_config["password"],
    }


@pytest.fixture(scope="session")
def timeout(test_config):
    return test_config.get("timeout", 10)
