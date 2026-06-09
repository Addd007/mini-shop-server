from pathlib import Path

import pytest

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader
from tests.common.context import TestContext
from tests.common.runner import CaseRunner


ROOT_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT_DIR / "cases"


@pytest.fixture(scope="session")
def case_loader():
    return CaseLoader(CASES_DIR)


@pytest.fixture(scope="session")
def context():
    return TestContext()


@pytest.fixture(scope="session")
def runner(base_url, timeout, context):
    client = ApiClient(base_url, timeout=timeout)
    return CaseRunner(client, context=context)


@pytest.mark.smoke
def test_yaml_smoke_cases(case_loader, runner):
    cases = case_loader.load("auth/auth_cases.yaml")
    assert cases
    for case in cases:
        runner.run_case(case)
