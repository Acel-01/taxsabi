from decimal import Decimal

from engine import load_ruleset, calculate_full, run_counterfactual

ruleset = load_ruleset()


def test_worked_example():
    result = calculate_full(3_600_000, {"pension": 438_000}, ruleset)
    assert result["total_tax"] == Decimal("359160.00"), result
    assert result["chargeable_income"] == Decimal("3162000.00"), result


def test_band_boundaries():
    cases = [
        (0, Decimal("0.00")),
        (799_999, Decimal("0.00")),
        (800_000, Decimal("0.00")),
        (800_001, Decimal("0.15")),
        (2_999_999, Decimal("329999.85")),
        (3_000_000, Decimal("330000.00")),
        (3_000_001, Decimal("330000.18")),
        (50_000_000, Decimal("10430000.00")),
        (50_000_001, Decimal("10430000.25")),
    ]
    for income, expected in cases:
        result = calculate_full(income, {}, ruleset)
        assert result["total_tax"] == expected, (income, result["total_tax"], expected)


def test_rent_relief_cap():
    result = calculate_full(2_000_000, {"rent": 1_000_000}, ruleset)
    assert result["total_relief"] == Decimal("200000.00"), result

    result = calculate_full(2_000_000, {"rent": 5_000_000}, ruleset)
    assert result["total_relief"] == Decimal("500000.00"), result


def test_multiple_reliefs():
    result = calculate_full(
        4_000_000,
        {"rent": 1_200_000, "pension": 300_000, "life_insurance": 150_000},
        ruleset,
    )
    assert result["total_relief"] == Decimal("690000.00"), result


def test_reliefs_cannot_exceed_gross():
    result = calculate_full(1_000_000, {"rent": 20_000_000}, ruleset)
    assert result["chargeable_income"] == Decimal("500000.00"), result
    assert result["total_tax"] == Decimal("0.00"), result


def test_counterfactual():
    delta = run_counterfactual(
        3_600_000,
        {"rent": 438_000},
        "pension",
        200_000,
        ruleset,
    )
    assert delta["delta"] == Decimal("36000.00"), delta


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
