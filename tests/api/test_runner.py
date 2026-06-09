from tests.common.case_loader import CaseLoader


def load_cases():
    loader = CaseLoader("tests/cases")
    return {
        "auth": loader.load("auth/auth_cases.yaml"),
        "catalog": loader.load("catalog/catalog_cases.yaml"),
        "order": loader.load("order/order_cases.yaml"),
        "file": loader.load("file/file_cases.yaml"),
    }
