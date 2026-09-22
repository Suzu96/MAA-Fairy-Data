import json
from pathlib import Path


INPUT = Path(
    "data/sources/icyveins_all_character_teams.json"
)

OUTPUT = Path(
    "data/sources/icyveins_warning_summary.json"
)


def main():
    data = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

    pages = []

    for page in data.get("pages", []):
        warnings = page.get(
            "warnings",
            []
        )

        if not warnings:
            continue

        pages.append(
            {
                "core":
                    page.get("core"),

                "url":
                    page.get("url"),

                "warning_count":
                    len(warnings),

                "warnings":
                    warnings
            }
        )

    result = {
        "warning_page_count":
            len(pages),

        "warning_count":
            sum(
                item["warning_count"]
                for item in pages
            ),

        "pages":
            pages
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
        f"Warning pages: {len(pages)}"
    )

    print(
        f"Warnings: "
        f"{result['warning_count']}"
    )


if __name__ == "__main__":
    main()
