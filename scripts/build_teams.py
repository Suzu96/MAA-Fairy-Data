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


def ensure_team(
    database,
    members
):
    key = team_key(
        members
    )

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

    return database[key]


def set_core(
    team,
    core
):
    if not core:
        return

    current = team.get(
        "core"
    )

    if current is None:
        team["core"] = core
        return

    if current == core:
        return

    conflicts = team.setdefault(
        "core_conflicts",
        []
    )

    if core not in conflicts:
        conflicts.append(
            core
        )


def add_source(
    team,
    source
):
    source_identity = (
        source.get("site"),
        source.get("url"),
        source.get("section")
    )

    for existing in team["sources"]:

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

    team["sources"].append(
        source
    )


def load_game8(
    database
):
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

        team = ensure_team(
            database,
            members
        )

        set_core(
            team,
            item.get("core")
        )

        add_source(
            team,
            {
                "site": "Game8",
                "url": source["url"],
                "section":
                    item["section"],
                "page_fetched_at":
                    source["fetched_at"]
            }
        )


def load_icyveins(
    database
):
    source = json.loads(
        ICYVEINS_FILE.read_text(
            encoding="utf-8"
        )
    )

    page_core = source.get(
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

        fully_normalized = (
            item.get(
                "fully_normalized",
                False
            )
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

        team = ensure_team(
            database,
            members
        )

        if (
            page_core
            and page_core in members
        ):
            set_core(
                team,
                page_core
            )

        add_source(
            team,
            {
                "site": "Icy Veins",
                "url": source["url"],
                "section":
                    "Hoshimi Miyabi's Best Teams",
                "page_fetched_at":
                    source["fetched_at"]
            }
        )


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
            item["core"] or "",
            item["id"]
        )
    )

    core_detected_count = sum(
        1
        for team in teams
        if team.get("core")
    )

    core_missing_count = sum(
        1
        for team in teams
        if not team.get("core")
    )

    core_conflict_count = sum(
        1
        for team in teams
        if team.get(
            "core_conflicts"
        )
    )

    multi_source_count = sum(
        1
        for team in teams
        if team["source_count"] > 1
    )

    data = {
        "schema": 5,

        "generated_at": datetime.now(
            timezone.utc
        )
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),

        "team_count":
            len(teams),

        "core_detected_count":
            core_detected_count,

        "core_missing_count":
            core_missing_count,

        "core_conflict_count":
            core_conflict_count,

        "multi_source_count":
            multi_source_count,

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
        f"Teams: {len(teams)}"
    )

    print(
        f"Core detected: "
        f"{core_detected_count}"
    )

    print(
        f"Core missing: "
        f"{core_missing_count}"
    )

    print(
        f"Core conflicts: "
        f"{core_conflict_count}"
    )

    print(
        f"Multi-source teams: "
        f"{multi_source_count}"
    )


if __name__ == "__main__":
    main()
