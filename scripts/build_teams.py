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
            "recommended_for": [],
            "archetype": None,
            "priority": 0,
            "sources": [],
            "tags": [],
            "notes": ""
        }

    return database[key]


def add_recommended_for(
    team,
    character
):
    if not character:
        return

    if character not in team["members"]:
        return

    if character not in team[
        "recommended_for"
    ]:
        team[
            "recommended_for"
        ].append(
            character
        )


def add_source(
    team,
    source
):
    source_identity = (
        source.get("site"),
        source.get("url"),
        source.get("section"),
        source.get("recommended_for")
    )

    for existing in team["sources"]:

        existing_identity = (
            existing.get("site"),
            existing.get("url"),
            existing.get("section"),
            existing.get(
                "recommended_for"
            )
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

        core = item.get(
            "core"
        )

        add_recommended_for(
            team,
            core
        )

        add_source(
            team,
            {
                "site": "Game8",
                "url": source["url"],
                "section":
                    item["section"],
                "recommended_for":
                    core,
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
            add_recommended_for(
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
                "recommended_for":
                    page_core,
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
            -len(
                item["recommended_for"]
            ),
            item["id"]
        )
    )

    recommended_detected = sum(
        1
        for team in teams
        if team["recommended_for"]
    )

    recommended_missing = sum(
        1
        for team in teams
        if not team["recommended_for"]
    )

    multi_anchor_count = sum(
        1
        for team in teams
        if len(
            team["recommended_for"]
        ) > 1
    )

    multi_source_count = sum(
        1
        for team in teams
        if team["source_count"] > 1
    )

    data = {
        "schema": 6,

        "generated_at": datetime.now(
            timezone.utc
        )
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),

        "team_count":
            len(teams),

        "recommended_for_detected_count":
            recommended_detected,

        "recommended_for_missing_count":
            recommended_missing,

        "multi_anchor_team_count":
            multi_anchor_count,

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
        f"Recommended-for detected: "
        f"{recommended_detected}"
    )

    print(
        f"Recommended-for missing: "
        f"{recommended_missing}"
    )

    print(
        f"Multi-anchor teams: "
        f"{multi_anchor_count}"
    )

    print(
        f"Multi-source teams: "
        f"{multi_source_count}"
    )


if __name__ == "__main__":
    main()
