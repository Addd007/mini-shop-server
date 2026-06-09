from __future__ import annotations

from pathlib import Path

from tests.common.case_loader import CaseLoader


def test_order_cases_yaml_loads():
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    cases = loader.load('tests/cases/order/order_cases.yaml')
    assert len(cases) >= 5
    assert cases[0]['id'] == 'TC-ORDER-001'
