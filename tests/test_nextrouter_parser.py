"""Testes para parser NextRouter."""

from decimal import Decimal

import pytest

from app.integrations.nextrouter.parser import (
    normalize_customer,
    normalize_customer_balance,
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
