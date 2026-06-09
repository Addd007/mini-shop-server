from __future__ import annotations

from pathlib import Path

from tests.common.case_loader import CaseLoader


def test_file_cases_yaml_loads():
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    cases = loader.load('tests/cases/file/file_cases.yaml')
    assert len(cases) >= 3
    assert cases[0]['id'] == 'TC-FILE-001'
