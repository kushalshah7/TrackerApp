"""Allow the tracker production origin in its managed Neon Auth configuration."""

from dotenv import dotenv_values
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


ORIGIN = "https://tracker-app-two-swart.vercel.app"
ENDPOINT = "ep-solitary-water-avqyhdfb"


def main():
    env = dotenv_values("../.env.local")
    if not env.get("DATABASE_URL_UNPOOLED"):
        raise RuntimeError("DATABASE_URL_UNPOOLED is required")
    with psycopg.connect(env["DATABASE_URL_UNPOOLED"], row_factory=dict_row) as connection:
        rows = connection.execute(
            "select id, trusted_origins from neon_auth.project_config "
            "where endpoint_id = %s for update", (ENDPOINT,),
        ).fetchall()
        if len(rows) != 1:
            raise RuntimeError("Expected exactly one auth configuration for the tracker endpoint")
        origins = rows[0]["trusted_origins"] or []
        if not isinstance(origins, list):
            raise RuntimeError("Unexpected trusted-origin configuration; no change made")
        if ORIGIN not in origins:
            connection.execute(
                "update neon_auth.project_config set trusted_origins = %s, updated_at = now() "
                "where id = %s", (Jsonb([*origins, ORIGIN]), rows[0]["id"]),
            )
    print(f"Trusted production origin configured: {ORIGIN}")


if __name__ == "__main__":
    main()
