import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_FILE = Path(
    "data/sources/icyveins_synergy_miyabi.json"
)

OUTPUT_FILE = Path(
    "data/synergy.json"
)


def main():
    source = json.loads(
        SOURCE_FILE.read_text(
            encoding="utf-8"
        )
    )

    relations = []

    for item in source.get(
        "synergies",
        []
    ):
        reason = item.get(
            "source_reason"
        )

        shared_reason = item.get(
            "shared_reason"
        )

        effective_reason = (
            reason
            if reason
            else shared_reason
        )

        relation = {
            "core":
                item["core"],

            "partner":
                item["partner"],

            "tags": [],

            "reason_zh":
                None,

            "source_reason":
                effective_reason,

            "shared_group":
                item.get(
                    "shared_group"
                ),

            "source_count":
                1,

            "sources": [
                {
                    "site":
                        "Icy Veins",

                    "url":
                        source["url"],

                    "raw_partner":
                        item.get(
                            "raw_partner"
                        ),

                    "fetched_at":
                        source["fetched_at"]
                }
            ]
        }

        relations.append(
            relation
        )

    data = {
        "schema": 2,

        "generated_at":
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
            ),

        "relation_count":
            len(relations),

        "relations":
            relations
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
        f"{len(relations)} "
        f"synergy relations."
    )


if __name__ == "__main__":
    main()
