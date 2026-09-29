"""One-time guarded correction for imported Meeting record 1778."""

from dotenv import dotenv_values
import psycopg
from psycopg.rows import dict_row


def main() -> None:
    env = dotenv_values("../.env.local")
    url = env.get("DATABASE_URL_UNPOOLED")
    if not url:
        raise RuntimeError("DATABASE_URL_UNPOOLED is required")
    with psycopg.connect(url, row_factory=dict_row) as connection:
        row = connection.execute(
            "select data from tracker_entries where id = %s and module = %s for update",
            (1778, "weekly-meeting"),
        ).fetchone()
        if not row or row["data"].get("Date") != "2026-08-18":
            raise RuntimeError("The target Meeting row no longer matches the audited record")
        if row["data"].get("Month") == "August":
            print("Meeting 1778 was already corrected")
            return
        if row["data"].get("Month") != "September":
            raise RuntimeError("The target Month changed; no correction was made")
        connection.execute(
            "update tracker_entries set data = jsonb_set(data, '{Month}', to_jsonb(%s::text)), "
            "updated_at = now(), last_edited_at = now() where id = %s and module = %s",
            ("August", 1778, "weekly-meeting"),
        )
    print("Meeting 1778: Month corrected from September to August")


if __name__ == "__main__":
    main()
