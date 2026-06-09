from pathlib import Path

import pytest

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader
from tests.common.context import TestContext
from tests.common.runner import CaseRunner


ROOT_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT_DIR / "cases"


@pytest.fixture(scope="function")
def yaml_runner(base_url, timeout):
    context = TestContext()
    client = ApiClient(base_url, timeout=timeout)
    return CaseRunner(client, context=context)


@pytest.mark.regression
@pytest.mark.order
def test_order_yaml_cases(yaml_runner):
    loader = CaseLoader(CASES_DIR)
    cases = loader.load("order/order_cases.yaml")
    assert cases
    for case in cases:
        yaml_runner.run_case(case)
