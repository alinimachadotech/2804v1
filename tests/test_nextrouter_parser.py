"""Testes para parser NextRouter."""

from decimal import Decimal

import pytest

from app.integrations.nextrouter.parser import (
    normalize_customer,
    normalize_customer_balance,
    normalize_report_payload,
    parse_money,
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("177,90", Decimal("177.90")),
        ("177.90", Decimal("177.90")),
        ("1.177,90", Decimal("1177.90")),
        ("1,177.90", Decimal("1177.90")),
        (177, Decimal("177")),
    ],
)
def test_parse_money_accepts_comma_and_dot(raw_value, expected):
    assert parse_money(raw_value) == expected


def test_normalize_customer_balance_uses_decimal():
    payload = {"id_cliente": "customer-1", "saldo": "177,90"}

    result = normalize_customer_balance(payload)

    assert result["customer_id"] == "customer-1"
    assert result["balance"] == Decimal("177.90")


def test_normalize_customer_balance_prioritizes_usable_balance():
    payload = {
        "id_cliente": "customer-1",
        "usable_balance": "177,90",
        "customer_balance": "77,90",
        "customer_limit": "100,00",
        "tipo_tar": 2,
    }

    result = normalize_customer_balance(payload)

    assert result["customer_id"] == "customer-1"
    assert result["balance"] == Decimal("177.90")
    assert result["usable_balance"] == Decimal("177.90")
    assert result["customer_balance"] == Decimal("77.90")
    assert result["customer_limit"] == Decimal("100.00")
    assert result["tipo_tar"] == 2


def test_normalize_customer_balance_falls_back_to_customer_balance():
    payload = {
        "id_cliente": "customer-1",
        "customer_balance": "77,90",
        "customer_limit": "100,00",
    }

    result = normalize_customer_balance(payload)

    assert result["balance"] == Decimal("77.90")
    assert result["usable_balance"] is None
    assert result["customer_balance"] == Decimal("77.90")
    assert result["customer_limit"] == Decimal("100.00")


def test_normalize_customer_balance_falls_back_to_legacy_balance_fields():
    payload = {"id_cliente": "customer-1", "saldo": "55,25"}

    result = normalize_customer_balance(payload)

    assert result["balance"] == Decimal("55.25")
    assert result["usable_balance"] is None
    assert result["customer_balance"] is None
    assert result["customer_limit"] is None


def test_normalize_customer_uses_nome_fantasia_then_razao_social():
    result = normalize_customer(
        {
            "id_cliente": "179",
            "nome_fantasia": "Cliente Fantasia",
            "razao_social": "Cliente Razao",
        }
    )

    assert result["customer_id"] == "179"
    assert result["name"] == "Cliente Fantasia"

    result = normalize_customer({"id_cliente": "179", "razao_social": "Cliente Razao"})

    assert result["name"] == "Cliente Razao"


def test_normalize_customer_name_falls_back_to_customer_id():
    result = normalize_customer({"id_cliente": "179"})

    assert result["name"] == "179"


def test_normalize_report_payload_preserves_totals_and_data():
    payload = {
        "total_records": 2,
        "records": 2,
        "total_time": "00:01:00",
        "total_time_text": "1 minuto",
        "total_value": "10,50",
        "total_cost_value": "6,25",
        "total_profit_on_ass": "4,25",
        "data": [{"valor": "10,50", "cost": "6,25"}],
    }

    result = normalize_report_payload(payload)

    assert result["total_records"] == 2
    assert result["records"] == 2
    assert result["total_time"] == "00:01:00"
    assert result["total_time_text"] == "1 minuto"
    assert result["total_value"] == "10,50"
    assert result["total_cost_value"] == "6,25"
    assert result["total_profit_on_ass"] == "4,25"
    assert result["data"] == [
        {"valor": Decimal("10.50"), "cost": Decimal("6.25")}
    ]
