import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_FILE = Path(
    "data/sources/icyveins_all_character_synergy.json"
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
    seen = set()

    for item in source.get(
        "relations",
        []
    ):
        core = item.get("core")
        partner = item.get("partner")

        if not core or not partner:
            continue

        if core == partner:
            continue

        key = (
            core,
            partner
        )

        if key in seen:
            continue

        seen.add(key)

        source_reason = (
            item.get(
                "source_reason"
            )
            or ""
        ).strip()

        if source_reason:
            evidence_type = (
                "explicit_reason"
            )

            reason_zh = None

        else:
            evidence_type = (
                "recommended_pairing"
            )

            reason_zh = (
                f"Icy Veins 将"
                f"{partner}列为"
                f"{core}的推荐搭档。"
            )

            source_reason = None

        relations.append(
            {
                "core":
                    core,

                "partner":
                    partner,

                "tags":
                    [],

                "reason_zh":
                    reason_zh,

                "source_reason":
                    source_reason,

                "evidence_type":
                    evidence_type,

                "source_count":
                    1,

                "sources": [
                    {
                        "site":
                            "Icy Veins",

                        "url":
                            item.get(
                                "url"
                            ),

                        "raw_partner":
                            item.get(
                                "raw_partner"
                            ),

                        "fetched_at":
                            source.get(
                                "fetched_at"
                            )
                    }
                ]
            }
        )

    explicit_count = sum(
        1
        for item in relations
        if item[
            "evidence_type"
        ] == "explicit_reason"
    )

    listing_count = sum(
        1
        for item in relations
        if item[
            "evidence_type"
        ] == "recommended_pairing"
    )

    data = {
        "schema": 4,

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

        "explicit_reason_count":
            explicit_count,

        "listing_only_count":
            listing_count,

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
        "Relations:",
        len(relations)
    )

    print(
        "Explicit reasons:",
        explicit_count
    )

    print(
        "Listing only:",
        listing_count
    )


if __name__ == "__main__":
    main()
