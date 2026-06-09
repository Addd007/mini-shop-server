from __future__ import annotations

from pathlib import Path

from tests.common.case_loader import CaseLoader


def test_catalog_cases_yaml_loads():
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    cases = loader.load('tests/cases/catalog/catalog_cases.yaml')
    assert len(cases) >= 4
    assert cases[0]['id'] == 'TC-PROD-001'
