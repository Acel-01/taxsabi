from __future__ import annotations

import re
from decimal import Decimal


_FULL_TOKEN = re.compile(
    r"^(?:(?:ngn|n|₦)\s*)?"
    r"([0-9]+(?:\.[0-9]+)?)\s*"
    r"(k|thousand|m|million|b|billion)?$",
    re.IGNORECASE,
)

_SEARCH_TOKEN = re.compile(
    r"(?:\b(?:ngn|n)\s*₦?\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:k|thousand|m|million|b|billion)?\b)"
    r"|(?:₦\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:k|thousand|m|million|b|billion)?\b)"
    r"|(?:\b[0-9]+(?:\.[0-9]+)?\s*(?:k|thousand|m|million|b|billion)\b)",
    re.IGNORECASE,
)

_MULTIPLIERS = {
    "k": Decimal("1000"),
    "thousand": Decimal("1000"),
    "m": Decimal("1000000"),
    "million": Decimal("1000000"),
    "b": Decimal("1000000000"),
    "billion": Decimal("1000000000"),
}

_MONTHLY_PERIOD = re.compile(r"\b(monthly|per month|every month|each month|a month)\b", re.IGNORECASE)
_ANNUAL_PERIOD = re.compile(r"\b(annual|annually|yearly|per year|every year|a year)\b", re.IGNORECASE)


def parse_money(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if not isinstance(value, str):
        raise TypeError(f"unsupported money value: {type(value).__name__}")

    normalized = value.strip().lower().replace(",", "")
    match = _FULL_TOKEN.fullmatch(normalized)
    if not match:
        raise ValueError(f"not a supported money token: {value!r}")
    amount = Decimal(match.group(1))
    suffix = match.group(2)
    return amount * _MULTIPLIERS.get(suffix, Decimal("1"))


def find_money_tokens(text: str) -> list[tuple[str, Decimal]]:
    return [(match.group(0), parse_money(match.group(0))) for match in _SEARCH_TOKEN.finditer(text)]


def detect_income_period(text: str) -> str | None:
    monthly = bool(_MONTHLY_PERIOD.search(text))
    annual = bool(_ANNUAL_PERIOD.search(text))
    if monthly and annual:
        raise ValueError("income period is ambiguous: both monthly and annual terms were found")
    if monthly:
        return "monthly"
    if annual:
        return "annual"
    return None


def annualize_income(amount, period: str) -> Decimal:
    value = parse_money(amount)
    normalized = period.strip().lower()
    if normalized == "monthly":
        return value * Decimal("12")
    if normalized == "annual":
        return value
    raise ValueError(f"unsupported income period: {period!r}")
