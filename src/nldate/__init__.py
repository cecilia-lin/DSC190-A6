# src/nldate/__init__.py
import re
from datetime import date
from dateutil.relativedelta import relativedelta
from dateutil import parser as dt_parser

# Dictionary to handle basic word-to-number conversion
WORD_TO_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
               "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

def parse(s: str, today: date | None = None) -> date:
    """
    Parses a natural language date string into a datetime.date object.
    """
    if today is None:
        today = date.today()

    s = s.lower().strip()

    # 1. Complex relative offsets: "X before/after/from Y"
    match = re.search(r'(.+?)\s+(before|after|from)\s+(.+)', s)
    if match:
        delta_str, direction, base_str = match.groups()
        base_date = _parse_base(base_str, today)
        delta = _parse_delta(delta_str)
        
        if direction == "before":
            return base_date - delta
        else:
            return base_date + delta

    # 2. Simple relative offsets: "X ago" or "in X"
    if match := re.search(r'(.+?)\s+ago', s):
        return today - _parse_delta(match.group(1))
    
    if match := re.search(r'in\s+(.+)', s):
        return today + _parse_delta(match.group(1))

    # 3. Base cases (today, tomorrow, next tuesday, exact dates)
    return _parse_base(s, today)

def _parse_base(s: str, today: date) -> date:
    """Helper to parse base targets like 'yesterday' or 'December 1st, 2025'"""
    s = s.strip()
    
    if s == "today":
        return today
    if s == "tomorrow":
        return today + relativedelta(days=1)
    if s == "yesterday":
        return today - relativedelta(days=1)

    # Handle "next <weekday>"
    if match := re.match(r'next\s+([a-z]+)', s):
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, 
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }
        target_day = weekdays.get(match.group(1))
        if target_day is not None:
            days_ahead = target_day - today.weekday()
            if days_ahead <= 0: # Target is next week
                days_ahead += 7
            return today + relativedelta(days=days_ahead)

    # Fallback to dateutil's standard parser for absolute dates
    try:
        return dt_parser.parse(s).date()
    except (ValueError, OverflowError):
        raise ValueError(f"Could not understand the date format: '{s}'")

def _parse_delta(s: str) -> relativedelta:
    """Helper to extract a time delta from strings like '1 year and 2 months'"""
    deltas = {"days": 0, "weeks": 0, "months": 0, "years": 0}
    
    # Replace spelled out numbers with digits (e.g., "two" -> "2")
    for word, num in WORD_TO_NUM.items():
        s = s.replace(word, str(num))
        
    # Find all occurrences of "number unit", ignoring pluralization
    matches = re.findall(r'(\d+)\s+(day|week|month|year)s?', s)
    
    for val, unit in matches:
        deltas[unit + "s"] += int(val)
        
    # Explicitly pass the arguments so Mypy knows exactly what types are going where
    return relativedelta(
        days=deltas["days"],
        weeks=deltas["weeks"],
        months=deltas["months"],
        years=deltas["years"]
    )
