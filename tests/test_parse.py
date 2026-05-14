from datetime import date

import pytest

from nldate import parse

TODAY = date(2025, 6, 11) 


def test_today() -> None:
    assert parse("today", today=TODAY) == TODAY


def test_tomorrow() -> None:
    assert parse("tomorrow", today=TODAY) == date(2025, 6, 12)


def test_yesterday() -> None:
    assert parse("yesterday", today=TODAY) == date(2025, 6, 10)


def test_iso_format() -> None:
    assert parse("2025-01-15") == date(2025, 1, 15)


def test_named_month() -> None:
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_next_tuesday() -> None:
    assert parse("next Tuesday", today=TODAY) == date(2025, 6, 17)


def test_last_monday() -> None:
    assert parse("last Monday", today=TODAY) == date(2025, 6, 9)


def test_in_3_days() -> None:
    assert parse("in 3 days", today=TODAY) == date(2025, 6, 14)


def test_2_weeks_ago() -> None:
    assert parse("2 weeks ago", today=TODAY) == date(2025, 5, 28)


def test_days_before_named_date() -> None:
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse("not a date")
