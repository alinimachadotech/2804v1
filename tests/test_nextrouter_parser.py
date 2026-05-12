"""Testes para parser NextRouter."""

from decimal import Decimal

import pytest

from app.integrations.nextrouter.parser import (
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
