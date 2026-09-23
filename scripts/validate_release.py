import json
from pathlib import Path


TEAMS_FILE = Path(
    "data/teams.json"
)

SYNERGY_FILE = Path(
    "data/synergy.json"
)


def fail(message):
    raise RuntimeError(message)


def validate_teams():
    data = json.loads(
        TEAMS_FILE.read_text(
            encoding="utf-8"
        )
    )

    teams = data.get(
        "teams",
        []
    )

    if len(teams) < 100:
        fail(
            "Team database unexpectedly small."
        )

    ids = set()

    for team in teams:
        team_id = team.get("id")

        if not team_id:
            fail(
                "Team missing id."
            )

        if team_id in ids:
            fail(
                f"Duplicate team id: {team_id}"
            )

        ids.add(team_id)

        members = team.get(
            "members",
            []
        )

        if len(members) != 3:
            fail(
                f"Invalid team size: {team_id}"
            )

        if len(set(members)) != 3:
            fail(
                f"Duplicate member in team: {team_id}"
            )

        if any(
            not member
            for member in members
        ):
            fail(
                f"Empty team member: {team_id}"
            )

    print(
        f"Teams OK: {len(teams)}"
    )


def validate_synergy():
    data = json.loads(
        SYNERGY_FILE.read_text(
            encoding="utf-8"
        )
    )

    relations = data.get(
        "relations",
        []
    )

    if len(relations) < 100:
        fail(
            "Synergy database unexpectedly small."
        )

    seen = set()

    for relation in relations:

        core = relation.get(
            "core"
        )

        partner = relation.get(
            "partner"
        )

        if not core or not partner:
            fail(
                "Synergy relation missing character."
            )

        if core == partner:
            fail(
                f"Self synergy detected: {core}"
            )

        key = (
            core,
            partner
        )

        if key in seen:
            fail(
                f"Duplicate synergy: {core} -> {partner}"
            )

        seen.add(key)

        evidence_type = relation.get(
            "evidence_type"
        )

        if evidence_type not in {
            "explicit_reason",
            "recommended_pairing"
        }:
            fail(
                f"Invalid evidence type: {key}"
            )

        if not relation.get(
            "reason_zh"
        ):
            fail(
                f"Missing Chinese reason: {key}"
            )

    print(
        f"Synergy OK: {len(relations)}"
    )


def main():
    validate_teams()
    validate_synergy()

    print(
        "Release validation passed."
    )


if __name__ == "__main__":
    main()
