"""Convert the privately saved invitation codes into employee signup links."""

import argparse
import csv
from pathlib import Path
from urllib.parse import quote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    with args.source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with args.destination.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["work_email", "private_signup_link"])
        for row in rows:
            writer.writerow([row["work_email"],
                             "https://tracker-app-two-swart.vercel.app/#invite="
                             + quote(row["one_time_invitation_code"], safe="")])
    print(f"Saved {len(rows)} private signup links to {args.destination}")


if __name__ == "__main__":
    main()
