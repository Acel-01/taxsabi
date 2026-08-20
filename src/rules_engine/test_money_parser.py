from decimal import Decimal

from money_parser import annualize_income, detect_income_period, find_money_tokens, parse_money


def test_shorthand_tokens():
    assert parse_money("1.6m") == Decimal("1600000")
    assert parse_money("500k") == Decimal("500000")
    assert parse_money("NGN 1.2 million") == Decimal("1200000")
    assert parse_money("₦2,500,000") == Decimal("2500000")
    assert parse_money("300000") == Decimal("300000")


def test_find_money_tokens():
    found = find_money_tokens("I earn 1.6m and pay 500k rent every year")
    assert found == [("1.6m", Decimal("1600000")), ("500k", Decimal("500000"))]


def test_income_period():
    assert detect_income_period("I earn 200k every month") == "monthly"
    assert detect_income_period("my salary is 2.4m a year") == "annual"
    assert detect_income_period("I earn 200k") is None
    assert annualize_income("200k", "monthly") == Decimal("2400000")


def test_ambiguous_period():
    try:
        detect_income_period("NGN 200k monthly and NGN 2.4m yearly")
    except ValueError:
        return
    raise AssertionError("expected ambiguous period to fail")


if __name__ == "__main__":
    test_shorthand_tokens()
    test_find_money_tokens()
    test_income_period()
    test_ambiguous_period()
    print("all money parser tests passed")
