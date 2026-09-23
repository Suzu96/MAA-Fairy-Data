import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_FILE = Path(
    "manifest.json"
)

TEAMS_FILE = Path(
    "data/teams.json"
)

SYNERGY_FILE = Path(
    "data/synergy.json"
)


VOLATILE_KEYS = {
    "generated_at",
    "fetched_at",
    "page_fetched_at"
}


def remove_volatile(value):
    if isinstance(value, dict):
        return {
            key: remove_volatile(item)
            for key, item in value.items()
            if key not in VOLATILE_KEYS
        }

    if isinstance(value, list):
        return [
            remove_volatile(item)
            for item in value
        ]

    return value


def semantic_hash(*objects):
    cleaned = [
        remove_volatile(obj)
        for obj in objects
    ]

    payload = json.dumps(
        cleaned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


def main():
    manifest = json.loads(
        MANIFEST_FILE.read_text(
            encoding="utf-8"
        )
    )

    teams = json.loads(
        TEAMS_FILE.read_text(
            encoding="utf-8"
        )
    )

    synergy = json.loads(
        SYNERGY_FILE.read_text(
            encoding="utf-8"
        )
    )

    new_hash = semantic_hash(
        teams,
        synergy
    )

    old_hash = manifest.get(
        "content_hash"
    )

    old_version = int(
        manifest.get(
            "database_version",
            0
        )
    )

    changed = (
        new_hash != old_hash
    )

    if changed:
        manifest[
            "database_version"
        ] = old_version + 1

        manifest[
            "updated_at"
        ] = (
            datetime.now(
                timezone.utc
            )
            .replace(
                microsecond=0
            )
            .isoformat()
            .replace(
                "+00:00",
                "Z"
            )
        )

    manifest[
        "content_hash"
    ] = new_hash

    manifest[
        "team_count"
    ] = teams.get(
        "team_count",
        len(
            teams.get(
                "teams",
                []
            )
        )
    )

    manifest[
        "synergy_relation_count"
    ] = synergy.get(
        "relation_count",
        len(
            synergy.get(
                "relations",
                []
            )
        )
    )

    MANIFEST_FILE.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        "Changed:",
        changed
    )

    print(
        "Database version:",
        manifest[
            "database_version"
        ]
    )

    print(
        "Team count:",
        manifest[
            "team_count"
        ]
    )

    print(
        "Synergy relations:",
        manifest[
            "synergy_relation_count"
        ]
    )


if __name__ == "__main__":
    main()
