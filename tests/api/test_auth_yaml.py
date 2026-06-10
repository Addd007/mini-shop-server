from __future__ import annotations

from pathlib import Path

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader
from tests.common.runner import YamlCaseRunner


def test_auth_cases_yaml_loads():
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    cases = loader.load('tests/cases/auth/auth_cases.yaml')
    assert len(cases) >= 4
    assert cases[0]['id'] == 'TC-AUTH-001'


def test_auth_cases_yaml_runner_smoke(base_url, timeout):
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    cases = loader.load('tests/cases/auth/auth_cases.yaml')
    client = ApiClient(base_url=base_url, timeout=timeout)
    runner = YamlCaseRunner(client)
    results = runner.run_cases(cases[:1])
    assert results[0].case_id == 'TC-AUTH-001'
    assert results[0].success is True
