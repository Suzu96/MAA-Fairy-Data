import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


GAME8_FILE = Path(
    "data/sources/game8_all_teams.json"
)

ICYVEINS_FILE = Path(
    "data/sources/icyveins_all_teams.json"
)

OUTPUT_FILE = Path(
    "data/teams.json"
)


def make_team_id(members):
    key = "|".join(
        sorted(members)
    )

    digest = hashlib.sha1(
        key.encode("utf-8")
    ).hexdigest()[:12]

    return f"team_{digest}"


def team_key(members):
    return tuple(
        sorted(members)
    )


def add_source(
    database,
    members,
    source
):
    key = team_key(members)

    if key not in database:
        database[key] = {
            "id": make_team_id(
                members
            ),
            "members": members,
            "core": None,
            "archetype": None,
            "priority": 0,
            "sources": [],
            "tags": [],
            "notes": ""
        }

    existing_sources = (
        database[key]["sources"]
    )

    source_identity = (
        source.get("site"),
        source.get("url"),
        source.get("section")
    )

    for existing in existing_sources:
        existing_identity = (
            existing.get("site"),
            existing.get("url"),
            existing.get("section")
        )

        if (
            existing_identity
            == source_identity
        ):
            return

    existing_sources.append(
        source
    )


def load_game8(database):
    source = json.loads(
        GAME8_FILE.read_text(
            encoding="utf-8"
        )
    )

    unmapped = source.get(
        "unmapped_names",
        []
    )

    if unmapped:
        raise RuntimeError(
            "Game8 still has unmapped "
            "character names: "
            + ", ".join(unmapped)
        )

    for item in source.get(
        "teams",
        []
    ):
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

        add_source(
            database,
            members,
            {
                "site": "Game8",
                "url": source["url"],
                "section":
                    item["section"],
                "page_fetched_at":
                    source["fetched_at"]
            }
        )


def load_icyveins(database):
    source = json.loads(
        ICYVEINS_FILE.read_text(
            encoding="utf-8"
        )
    )

    core = source.get(
        "core"
    )

    for item in source.get(
        "teams",
        []
    ):
        members = item.get(
            "normalized_members",
            []
        )

        fully_normalized = item.get(
            "fully_normalized",
            False
        )

        if not fully_normalized:
            continue

        if len(members) != 3:
            continue

        if any(
            member is None
            for member in members
        ):
            continue

        add_source(
            database,
            members,
            {
                "site": "Icy Veins",
                "url": source["url"],
                "section":
                    "Hoshimi Miyabi's Best Teams",
                "page_fetched_at":
                    source["fetched_at"]
            }
        )

        key = team_key(
            members
        )

        if (
            core
            and core in members
        ):
            database[key]["core"] = core


def main():
    database = {}

    load_game8(
        database
    )

    load_icyveins(
        database
    )

    teams = []

    for team in database.values():
        team["source_count"] = len(
            team["sources"]
        )

        teams.append(
            team
        )

    teams.sort(
        key=lambda item: (
            -item["source_count"],
            item["id"]
        )
    )

    data = {
        "schema": 4,

        "generated_at": datetime.now(
            timezone.utc
        )
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),

        "team_count":
            len(teams),

        "teams":
            teams
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
        f"Generated "
        f"{len(teams)} merged teams."
    )

    multi_source = [
        team
        for team in teams
        if team["source_count"] > 1
    ]

    print(
        f"Multi-source teams: "
        f"{len(multi_source)}"
    )

    for team in multi_source:
        print(
            " + ".join(
                team["members"]
            ),
            "=>",
            team["source_count"],
            "sources"
        )


if __name__ == "__main__":
    main()
