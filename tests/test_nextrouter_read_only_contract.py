"""Contract tests that keep NextRouter integration strictly read-only."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEXTROUTER_ENDPOINT_MODULES = [
    ROOT / "app" / "api" / "v1" / "endpoints" / "customers.py",
    ROOT / "app" / "api" / "v1" / "endpoints" / "contacts.py",
    ROOT / "app" / "api" / "v1" / "endpoints" / "online_calls.py",
    ROOT / "app" / "api" / "v1" / "endpoints" / "reports.py",
]


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_nextrouter_related_endpoints_do_not_expose_mutation_routes():
    forbidden_decorators = {"post", "delete"}

    for path in NEXTROUTER_ENDPOINT_MODULES:
        tree = ast.parse(_source(path), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr in forbidden_decorators
                    and isinstance(func.value, ast.Name)
                    and func.value.id.endswith("router")
                ):
                    raise AssertionError(
                        f"{path.relative_to(ROOT)} exposes @{func.value.id}.{func.attr}"
                    )


def test_nextrouter_client_does_not_expose_mutation_methods():
    from app.integrations.nextrouter.client import NextRouterClient

    forbidden_methods = {
        "set_customer_status",
        "manage_credit",
        "delete_online_call",
    }

    for method_name in forbidden_methods:
        assert not hasattr(NextRouterClient, method_name)


def test_services_and_schemas_do_not_expose_mutation_contracts():
    from app.schemas import financial
    from app.services import customer_service, financial_service

    forbidden_customer_service = {
        "activate_customer",
        "deactivate_customer",
        "set_customer_status",
    }
    forbidden_financial_service = {
        "credit_customer",
        "debit_customer",
        "set_customer_credit",
    }
    forbidden_financial_schemas = {
        "FinancialOperationIn",
    }

    for name in forbidden_customer_service:
        assert not hasattr(customer_service, name)
    for name in forbidden_financial_service:
        assert not hasattr(financial_service, name)
    for name in forbidden_financial_schemas:
        assert not hasattr(financial, name)


def test_reports_service_exposes_read_only_report_functions():
    from app.services import reports_service

    expected_functions = {
        "get_cdr_report",
        "get_cdr_disconnection_report",
        "get_cdr_sipcodes_report",
        "get_profit_customers_report",
        "get_profit_gateways_report",
    }

    for name in expected_functions:
        assert callable(getattr(reports_service, name, None))


def test_nextrouter_endpoints_do_not_define_status_customer():
    source = _source(ROOT / "app" / "integrations" / "nextrouter" / "endpoints.py")

    assert "STATUS_CUSTOMER" not in source


def test_nextrouter_integration_uses_no_mutating_http_calls():
    integration_root = ROOT / "app" / "integrations" / "nextrouter"
    forbidden_calls = {
        ("client", "post"),
        ("client", "delete"),
        ("requests", "post"),
        ("requests", "delete"),
    }

    for path in integration_root.glob("*.py"):
        tree = ast.parse(_source(path), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if not isinstance(node.func.value, ast.Name):
                continue

            call = (node.func.value.id, node.func.attr)
            assert call not in forbidden_calls, (
                f"{path.relative_to(ROOT)} uses mutating HTTP call "
                f"{node.func.value.id}.{node.func.attr}"
            )
