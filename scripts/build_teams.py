import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_FILE = Path("data/sources/game8_all_teams.json")
OUTPUT_FILE = Path("data/teams.json")


def make_team_id(members):
    key = "|".join(sorted(members))

    digest = hashlib.sha1(
        key.encode("utf-8")
    ).hexdigest()[:12]

    return f"team_{digest}"


def main():
    source = json.loads(
        SOURCE_FILE.read_text(
            encoding="utf-8"
        )
    )

    unmapped = source.get(
        "unmapped_names",
        []
    )

    if unmapped:
        raise RuntimeError(
            "Unmapped character names remain: "
            + ", ".join(unmapped)
        )

    source_teams = source.get(
        "teams",
        []
    )

    output_teams = []

    seen = set()

    for item in source_teams:

        members = item.get(
            "normalized_members",
            []
        )

        if len(members) != 3:
            continue

        if any(
            member is None
            for member in members
        ):
            continue

        dedupe_key = tuple(
            sorted(members)
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)

        team = {
            "id": make_team_id(
                members
            ),

            "members": members,

            "core": None,

            "archetype": None,

            "priority": 0,

            "source_count": 1,

            "sources": [
                {
                    "site": "Game8",
                    "url": source["url"],
                    "section": item["section"],
                    "page_fetched_at":
                        source["fetched_at"]
                }
            ],

            "tags": [],

            "notes": ""
        }

        output_teams.append(team)

    data = {
        "schema": 2,

        "generated_at": datetime.now(
            timezone.utc
        )
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),

        "team_count":
            len(output_teams),

        "teams":
            output_teams
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        f"Generated {len(output_teams)} "
        f"normalized teams."
    )


if __name__ == "__main__":
    main()
