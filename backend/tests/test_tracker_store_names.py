from app.tracker_store import PRESALES_NAMES, canonical_full_names


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
