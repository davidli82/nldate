from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

MONTHS: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

WORD_NUMBERS: dict[str, int] = {
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
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
}


def _parse_num(s: str) -> int | None:
    if s.isdigit():
        return int(s)
    return WORD_NUMBERS.get(s)


def _next_weekday(ref: date, wd: int) -> date:
    days = wd - ref.weekday()
    if days <= 0:
        days += 7
    return ref + timedelta(days=days)


def _last_weekday(ref: date, wd: int) -> date:
    days = ref.weekday() - wd
    if days <= 0:
        days += 7
    return ref - timedelta(days=days)


def _this_weekday(ref: date, wd: int) -> date:
    days = wd - ref.weekday()
    if days < 0:
        days += 7
    return ref + timedelta(days=days)


def _apply_offset(base: date, amount: int, unit: str, sign: int) -> date:
    unit = unit.rstrip("s")
    if unit == "day":
        return base + timedelta(days=sign * amount)
    if unit == "week":
        return base + timedelta(weeks=sign * amount)
    if unit == "month":
        m = base.month + sign * amount
        y = base.year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        d = min(base.day, calendar.monthrange(y, m)[1])
        return date(y, m, d)
    if unit == "year":
        try:
            return base.replace(year=base.year + sign * amount)
        except ValueError:
            return base.replace(year=base.year + sign * amount, day=28)
    raise ValueError(f"Unknown unit: {unit}")


def _parse_offset_parts(s: str) -> list[tuple[int, str]] | None:
    num_pat = r"(?:\d+|" + "|".join(WORD_NUMBERS) + r")"
    unit_pat = r"(?:years?|months?|weeks?|days?)"
    pairs = re.findall(rf"({num_pat})\s+({unit_pat})", s)
    if not pairs:
        return None
    result = []
    for n_str, unit in pairs:
        n = _parse_num(n_str)
        if n is None:
            return None
        result.append((n, unit))
    return result


def _month_pattern() -> str:
    return "(?:" + "|".join(MONTHS) + r")\.?"


def _parse_anchor(s: str, today: date) -> date | None:
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today + timedelta(days=-1)
    if s == "the day after tomorrow":
        return today + timedelta(days=2)
    if s == "the day before yesterday":
        return today + timedelta(days=-2)

    # YYYY-MM-DD or YYYY/MM/DD
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # MM/DD/YYYY or MM-DD-YYYY
    m = re.fullmatch(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", s)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

    month_pat = _month_pattern()

    # "December 1st, 2025" or "Dec. 1, 2025"
    m = re.fullmatch(rf"({month_pat})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})", s)
    if m:
        mon_str = m.group(1).rstrip(".")
        return date(int(m.group(3)), MONTHS[mon_str], int(m.group(2)))

    # "1st December 2025"
    m = re.fullmatch(rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_pat})\s+(\d{{4}})", s)
    if m:
        mon_str = m.group(2).rstrip(".")
        return date(int(m.group(3)), MONTHS[mon_str], int(m.group(1)))

    # "December 2025" (no day)
    m = re.fullmatch(rf"({month_pat})\s+(\d{{4}})", s)
    if m:
        mon_str = m.group(1).rstrip(".")
        return date(int(m.group(2)), MONTHS[mon_str], 1)

    # "next/last/this weekday"
    m = re.fullmatch(r"(next|last|this)\s+(\w+)", s)
    if m:
        wd = WEEKDAYS.get(m.group(2))
        if wd is not None:
            if m.group(1) == "next":
                return _next_weekday(today, wd)
            if m.group(1) == "last":
                return _last_weekday(today, wd)
            return _this_weekday(today, wd)

    # bare weekday name
    wd = WEEKDAYS.get(s)
    if wd is not None:
        return _this_weekday(today, wd)

    return None


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()

    s = re.sub(r"\s+", " ", s.strip().lower())

    anchor = _parse_anchor(s, today)
    if anchor is not None:
        return anchor

    if s == "next month":
        return _apply_offset(today, 1, "month", 1)
    if s == "last month":
        return _apply_offset(today, 1, "month", -1)
    if s == "next year":
        return _apply_offset(today, 1, "year", 1)
    if s == "last year":
        return _apply_offset(today, 1, "year", -1)

    # "in N units"
    m = re.fullmatch(r"in\s+(.+)", s)
    if m:
        parts = _parse_offset_parts(m.group(1))
        if parts:
            result = today
            for amount, unit in parts:
                result = _apply_offset(result, amount, unit, 1)
            return result

    # "N units ago"
    m = re.fullmatch(r"(.+?)\s+ago", s)
    if m:
        parts = _parse_offset_parts(m.group(1))
        if parts:
            result = today
            for amount, unit in parts:
                result = _apply_offset(result, amount, unit, -1)
            return result

    # "N units from now"
    m = re.fullmatch(r"(.+?)\s+from\s+now", s)
    if m:
        parts = _parse_offset_parts(m.group(1))
        if parts:
            result = today
            for amount, unit in parts:
                result = _apply_offset(result, amount, unit, 1)
            return result

    # "N units before/after/from <anchor>"
    for kw, sign in [
        ("before", -1),
        ("prior to", -1),
        ("after", 1),
        ("from", 1),
        ("following", 1),
    ]:
        m = re.fullmatch(rf"(.+?)\s+{kw}\s+(.+)", s)
        if m:
            parts = _parse_offset_parts(m.group(1))
            anchor2 = _parse_anchor(m.group(2).strip(), today)
            if parts and anchor2:
                result = anchor2
                for amount, unit in parts:
                    result = _apply_offset(result, amount, unit, sign)
                return result

    # end of month/year/named month
    month_pat = _month_pattern()
    m = re.fullmatch(rf"end of (?:the )?({month_pat}|month|year)", s)
    if m:
        word = m.group(1).rstrip(".")
        if word == "month":
            last = calendar.monthrange(today.year, today.month)[1]
            return date(today.year, today.month, last)
        if word == "year":
            return date(today.year, 12, 31)
        mon = MONTHS.get(word)
        if mon:
            last = calendar.monthrange(today.year, mon)[1]
            return date(today.year, mon, last)

    # beginning/start of month/year/named month
    m = re.fullmatch(rf"(?:beginning|start) of (?:the )?({month_pat}|month|year)", s)
    if m:
        word = m.group(1).rstrip(".")
        if word == "month":
            return date(today.year, today.month, 1)
        if word == "year":
            return date(today.year, 1, 1)
        mon = MONTHS.get(word)
        if mon:
            return date(today.year, mon, 1)

    raise ValueError(f"Cannot parse date string: {s!r}")
