import re
from datetime import date
from dateutil.relativedelta import relativedelta
from dateutil import parser as dt_parser

# Expanded dictionary to catch common words
WORD_TO_NUM = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "dozen": 12,
    "couple": 2,
    "few": 3,
}


def parse(s: str, today: date | None = None) -> date:
    """
    Parses a natural language date string into a datetime.date object.
    """
    if today is None:
        today = date.today()

    s = s.lower().strip()

    # 0. Clean up tricky multi-word idioms manually before regex
    s = s.replace("the day after tomorrow", "in 2 days")
    s = s.replace("the day before yesterday", "2 days ago")
    s = s.replace("a couple of", "2")
    s = s.replace("a few", "3")

    # 1. Complex relative offsets: "X before/after/from Y"
    match = re.search(r"(.+?)\s+\b(before|after|from)\b\s+(.+)", s)
    if match:
        delta_str, direction, base_str = match.groups()
        base_date = _parse_base(base_str, today)
        delta = _parse_delta(delta_str)

        if direction == "before":
            return base_date - delta
        else:
            return base_date + delta

    # 2. Simple relative offsets: "X ago" or "in X"
    if match := re.search(r"(.+?)\s+ago\b", s):
        return today - _parse_delta(match.group(1))

    if match := re.search(r"\bin\s+(.+)", s):
        return today + _parse_delta(match.group(1))

    # 3. Base cases
    return _parse_base(s, today)


def _parse_base(s: str, today: date) -> date:
    """Helper to parse base targets like 'yesterday' or 'December 1st, 2025'"""
    s = s.strip()

    if s in ("today", "now"):
        return today
    if s == "tomorrow":
        return today + relativedelta(days=1)
    if s == "yesterday":
        return today - relativedelta(days=1)

    # Handle "next/last week/month/year"
    if match := re.match(r"(next|last|this)\s+(week|month|year)", s):
        direction, unit = match.groups()
        sign = 1 if direction in ("next", "this") else -1

        if unit == "week":
            return today + relativedelta(weeks=sign)
        elif unit == "month":
            return today + relativedelta(months=sign)
        elif unit == "year":
            return today + relativedelta(years=sign)

    # Handle "next/last/this <weekday>"
    if match := re.match(r"(next|last|this)\s+([a-z]+)", s):
        direction, day_name = match.groups()
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        target_day = weekdays.get(day_name)
        if target_day is not None:
            current_day = today.weekday()
            days_diff = target_day - current_day

            if direction == "next":
                if days_diff <= 0:
                    days_diff += 7
            elif direction == "last":
                if days_diff >= 0:
                    days_diff -= 7
            elif direction == "this":  # "this Tuesday" means the upcoming Tuesday
                if days_diff < 0:
                    days_diff += 7

            return today + relativedelta(days=days_diff)

    # Fallback to dateutil's standard parser for absolute dates
    try:
        return dt_parser.parse(s).date()
    except (ValueError, OverflowError):
        raise ValueError(f"Could not understand the date format: '{s}'")


def _parse_delta(s: str) -> relativedelta:
    """Helper to extract a time delta from strings like '1 year and 2 months'"""
    deltas = {"days": 0, "weeks": 0, "months": 0, "years": 0}

    for word, num in WORD_TO_NUM.items():
        s = re.sub(r"\b" + word + r"\b", str(num), s)

    # Find optional number and unit. If no number is found (e.g. "the day"), default to 1.
    matches = re.findall(r"\b(\d+)?\s*(day|week|month|year)s?\b", s)

    for val, unit in matches:
        num = int(val) if val else 1
        deltas[unit + "s"] += num

    return relativedelta(
        days=deltas["days"],
        weeks=deltas["weeks"],
        months=deltas["months"],
        years=deltas["years"],
    )
