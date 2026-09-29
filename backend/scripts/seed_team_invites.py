"""Create one-time tracker invitations without storing plaintext codes in Postgres."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import secrets
from pathlib import Path

import psycopg
from dotenv import dotenv_values


SCHEMA = """
create table if not exists tracker_invites (
    email text primary key,
    code_hash text not null,
    redeemed_user_id text unique,
    created_at timestamptz not null default now(),
    expires_at timestamptz not null,
    redeemed_at timestamptz
);
alter table tracker_invites enable row level security;
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("emails_file", type=Path, help="JSON array of approved emails")
    parser.add_argument("output", type=Path, help="Ignored CSV where plaintext codes are delivered once")
    args = parser.parse_args()
    emails = [str(item).strip().casefold() for item in json.loads(args.emails_file.read_text(encoding="utf-8"))]
    if len(emails) != 10 or len(set(emails)) != 10 or any("@" not in email for email in emails):
        raise ValueError("Exactly ten distinct approved email addresses are required")
    if args.output.exists():
        raise FileExistsError(args.output)
    env = dotenv_values("../.env.local")
    url = env.get("DATABASE_URL_UNPOOLED")
    if not url:
        raise RuntimeError("DATABASE_URL_UNPOOLED is required")

    invitations = [(email, secrets.token_urlsafe(24)) for email in emails]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["work_email", "one_time_invitation_code"])
        writer.writerows(invitations)
    try:
        with psycopg.connect(url) as connection:
            connection.execute(SCHEMA)
            for email, code in invitations:
                inserted = connection.execute(
                    "insert into tracker_invites(email, code_hash, expires_at) "
                    "values (%s, %s, now() + interval '90 days') "
                    "on conflict (email) do nothing returning email",
                    (email, hashlib.sha256(code.encode("utf-8")).hexdigest()),
                ).fetchone()
                if not inserted:
                    raise RuntimeError(f"An invitation already exists for {email}; no codes were changed")
    except Exception:
        args.output.unlink(missing_ok=True)
        raise
    print(f"Created {len(invitations)} invitations; codes saved only to {args.output}")


if __name__ == "__main__":
    main()
