from datetime import date, datetime, timezone

import pytest

from app.tracker_store import (
    ConflictError,
    PRESALES_NAMES,
    TrackerStore,
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
        "Irshad",
        "Kalim Ansari",
        "Pawan Dubey",
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
        "Noaman Vohra",
        "Noaman Vohara",
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
        "Noaman Vohara",
    ]


def test_distinct_people_with_the_same_first_name_stay_distinct():
    assert canonical_full_names(["Aisha", "Aisha Gupta", "Aisha Sharma"]) == [
        "Aisha Gupta", "Aisha Sharma",
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


def test_new_presales_must_match_the_roster():
    data = {"Presales": "ankesh singh"}
    TrackerStore._check_presales(data)
    assert data["Presales"] == "Ankesh Singh"

    with pytest.raises(ValueError, match="eight team names"):
        TrackerStore._check_presales({"Presales": "Unlisted Person"})

    # An imported ISP Team row can still be edited without changing its owner.
    TrackerStore._check_presales({"Presales": "Ananya Sharma"}, {"Presales": "Ananya Sharma"})


def test_stale_edit_or_delete_is_rejected():
    old = datetime(2026, 9, 1, tzinfo=timezone.utc)
    new = datetime(2026, 9, 2, tzinfo=timezone.utc)
    TrackerStore._check_version(old, old)
    TrackerStore._check_version(None, None)
    with pytest.raises(ConflictError, match="Refresh"):
        TrackerStore._check_version(new, old)


def test_account_manager_input_rejects_combined_and_placeholder_names():
    store = TrackerStore("postgresql://unused")
    base = {"Region": "West", "Presales": "Ankesh Singh", "Customer": "Acme",
            "Opportunity Details": "Discussion"}
    for name in ("Kratika/Ashritha", "Team", "NA"):
        with pytest.raises(ValueError, match="one person's name"):
            store._clean("weekly-review", {**base, "AM": name})
    assert store._clean("weekly-review", {**base, "AM": "Jai"})["AM"] == "Jaidrath Maniyar"


def test_meeting_month_follows_date_and_week_remains_manually_chosen():
    store = TrackerStore("postgresql://unused")
    data = {"Region": "West", "Date": date(2026, 8, 18), "Month": "September",
            "Week": "2", "Presales": "Pawan Dubey", "Account Name": "Example",
            "Meeting Agenda": "Follow-up"}
    clean = store._clean("weekly-meeting", data)
    assert clean["Date"] == "2026-08-18"
    assert clean["Month"] == "August"
    assert clean["Week"] == "2"

    with pytest.raises(ValueError, match="Week"):
        store._clean("weekly-meeting", {**data, "Week": ""})
