from datetime import date

import pytest

from app.tracker_store import (
    PRESALES_NAMES,
    canonical_full_names,
    excel_month_year,
    normalize_month_year,
)


def test_presales_roster_contains_only_the_eight_active_names():
    assert len(PRESALES_NAMES) == 8
    assert PRESALES_NAMES == (
        "Aditya Potdar",
        "Ankesh Singh",
        "Arun M",
        "Ayush Rajput",
        "Irshad",
        "Kalim Ansari",
        "Suraj Raskar",
        "Surender Kumar",
    )


def test_canonical_full_names_removes_short_and_case_variants():
    names = [
        "Darshana",
        "darshana",
        "Darshana Patil",
        "Darshana Patil",
        "Mohit",
        "Mohit Kapoor",
        "Mohit kapoor",
        "Ashritha",
        "Hrishi Sir",
        "Hrishikesh Phadnis",
        "Jai",
        "Jaidrath Maniyar",
        "Krathika",
        "Kratika",
        "Kratika/Ashritha",
        "Merlyn Methew",
        "Moihit Kapoor",
        "Navneet",
        "Navaneet",
        "NA",
        "Team",
    ]

    assert canonical_full_names(names) == [
        "Ashritha",
        "Darshana Patil",
        "Hrishikesh Phadnis",
        "Jaidrath Maniyar",
        "Kratika",
        "Merlyn Mathew",
        "Mohit Kapoor",
        "Navaneet",
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [("2026-09", "2026-09"), ("2026-09-15", "2026-09"), ("Sep-26", "2026-09")],
)
def test_normalize_month_year(value, expected):
    assert normalize_month_year(value) == expected


def test_excel_month_year_is_a_real_excel_date():
    assert excel_month_year("2026-09") == date(2026, 9, 1)


def test_normalize_month_year_rejects_invalid_values():
    with pytest.raises(ValueError, match="YYYY-MM"):
        normalize_month_year("Septemberish")
