# tests/test_parse.py
import pytest
from datetime import date
from nldate import parse

# A fixed "today" to act as our reference point for tests
REF_DATE = date(2024, 5, 10) # Friday

@pytest.mark.parametrize("input_str, expected", [
    # Base cases
    ("today", date(2024, 5, 10)),
    ("tomorrow", date(2024, 5, 11)),
    ("yesterday", date(2024, 5, 9)),
    
    # Exact dates
    ("December 1st, 2025", date(2025, 12, 1)),
    ("2024-10-31", date(2024, 10, 31)),
    
    # "Next" weekday
    ("next Tuesday", date(2024, 5, 14)),
    ("next Friday", date(2024, 5, 17)), 
    
    # Relative to today
    ("in 3 days", date(2024, 5, 13)),
    ("5 days ago", date(2024, 5, 5)),
    
    # Complex combinations (The boss's examples)
    ("5 days before December 1st, 2025", date(2025, 11, 26)),
    ("1 year and 2 months after yesterday", date(2025, 7, 9)),
    ("two weeks from tomorrow", date(2024, 5, 25)), 
])
def test_parse_valid_dates(input_str: str, expected: date) -> None:
    # We pass the REF_DATE as 'today' to ensure tests are deterministic
    assert parse(input_str, today=REF_DATE) == expected

def test_parse_defaults_to_actual_today() -> None:
    # Test that not passing a date defaults to actual today
    assert parse("today") == date.today()

def test_invalid_date_raises_error() -> None:
    # Test our guardrails
    with pytest.raises(ValueError):
        parse("some nonsense string")