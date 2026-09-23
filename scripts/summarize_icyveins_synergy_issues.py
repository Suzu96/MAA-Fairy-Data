import json
from collections import Counter
from pathlib import Path


INPUT = Path(
    "data/sources/icyveins_all_character_synergy.json"
)

OUTPUT = Path(
    "data/sources/icyveins_synergy_issue_summary.json"
)


def main():
    data = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

    empty_by_core = Counter()
    total_by_core = Counter()

    samples = []

    for item in data.get(
        "relations",
        []
    ):
        core = item.get(
            "core"
        )

        total_by_core[
            core
        ] += 1

        reason = (
            item.get(
                "source_reason"
            )
            or ""
        ).strip()

        if reason:
            continue

        empty_by_core[
            core
        ] += 1

        if len(samples) < 40:
            samples.append(
                {
                    "core":
                        core,

                    "partner":
                        item.get(
                            "partner"
                        ),

                    "raw_partner":
                        item.get(
                            "raw_partner"
                        ),

                    "url":
                        item.get(
                            "url"
                        )
                }
            )

    affected_cores = []

    for core, count in (
        empty_by_core.most_common()
    ):
        affected_cores.append(
            {
                "core":
                    core,

                "empty_count":
                    count,

                "total_count":
                    total_by_core[
                        core
                    ]
            }
        )

    result = {
        "relation_count":
            data.get(
                "relation_count",
                0
            ),

        "empty_reason_count":
            sum(
                empty_by_core.values()
            ),

        "affected_core_count":
            len(
                affected_cores
            ),

        "affected_cores":
            affected_cores,

        "samples":
            samples
    }

    OUTPUT.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        "Empty reasons:",
        result[
            "empty_reason_count"
        ]
    )

    print(
        "Affected cores:",
        result[
            "affected_core_count"
        ]
    )


if __name__ == "__main__":
    main()
