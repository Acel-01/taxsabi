import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RULES_PATH = Path(__file__).parent / "rules_ng_2026.json"
MONEY_PLACES = Decimal("0.01")


def decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def money(value):
    return decimal(value).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def load_ruleset(path=RULES_PATH):
    return json.loads(Path(path).read_text())


def apply_relief(relief_id, stated_amount, ruleset):
    if stated_amount is None:
        return Decimal("0")
    config = ruleset["reliefs"].get(relief_id)
    if config is None:
        raise ValueError(f"unknown relief: {relief_id}")
    if config["type"] == "percent_cap":
        return money(min(decimal(stated_amount) * decimal(config["percent"]), decimal(config["cap"])))
    return money(stated_amount)


def compute_chargeable_income(gross_annual, relief_inputs, ruleset):
    total_relief = sum(
        (apply_relief(rid, amount, ruleset) for rid, amount in relief_inputs.items()),
        Decimal("0"),
    )
    return max(Decimal("0"), money(gross_annual) - total_relief), money(total_relief)


def compute_tax(chargeable_income, ruleset):
    remaining = money(chargeable_income)
    breakdown = []
    total = Decimal("0")
    for band in ruleset["bands"]:
        upper = band["upper"]
        band_size = decimal(upper) - decimal(band["lower"]) if upper is not None else remaining
        taxed = min(remaining, band_size)
        if taxed <= 0:
            break
        tax = money(taxed * decimal(band["rate"]))
        breakdown.append({
            "band": f"{band['lower']:,} - {upper or 'inf'}",
            "rate": decimal(band["rate"]),
            "taxed_amount": money(taxed),
            "tax": tax,
        })
        total += tax
        remaining -= taxed
    return {"total_tax": money(total), "breakdown": breakdown}


def calculate_full(gross_annual, relief_inputs, ruleset):
    chargeable, total_relief = compute_chargeable_income(gross_annual, relief_inputs, ruleset)
    result = compute_tax(chargeable, ruleset)
    result["gross_annual"] = money(gross_annual)
    result["total_relief"] = money(total_relief)
    result["chargeable_income"] = money(chargeable)
    return result


def run_counterfactual(gross_annual, base_reliefs, changed_field, new_value, ruleset):
    base = calculate_full(gross_annual, base_reliefs, ruleset)
    scenario_reliefs = {**base_reliefs, changed_field: new_value}
    scenario = calculate_full(gross_annual, scenario_reliefs, ruleset)
    return {
        "base_tax": base["total_tax"],
        "scenario_tax": scenario["total_tax"],
        "delta": money(base["total_tax"] - scenario["total_tax"]),
        "scenario_chargeable_income": scenario["chargeable_income"],
    }
