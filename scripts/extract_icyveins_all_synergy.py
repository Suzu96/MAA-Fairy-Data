
import json
import re
import html
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


PAGES_FILE = Path(
    "data/sources/icyveins_team_pages.json"
)

ALIASES_FILE = Path(
    "data/name_aliases.json"
)

OUTPUT = Path(
    "data/sources/icyveins_all_character_synergy.json"
)


def clean_text(value):
    value = re.sub(
        r"<script[\s\S]*?</script>",
        " ",
        value,
        flags=re.I
    )

    value = re.sub(
        r"<style[\s\S]*?</style>",
        " ",
        value,
        flags=re.I
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = html.unescape(
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def fetch(url):
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/153 Safari/537.36"
            ),
            "Accept-Language":
                "en-US,en;q=0.9"
        }
    )

    with urlopen(
        request,
        timeout=30
    ) as response:

        return (
            response.status,
            response.read().decode(
                "utf-8",
                errors="replace"
            )
        )


def find_synergy_section(
    raw_html,
    raw_core
):
    headings = list(
        re.finditer(
            r"<h2\b[^>]*>(.*?)</h2>",
            raw_html,
            flags=re.I | re.S
        )
    )

    for index, match in enumerate(
        headings
    ):
        heading = clean_text(
            match.group(1)
        )

        lower = heading.lower()

        if (
            "best pairings and synergies"
            not in lower
        ):
            continue

        if raw_core.lower() not in lower:
            continue

        start = match.end()

        if index + 1 < len(headings):
            end = headings[
                index + 1
            ].start()
        else:
            end = len(raw_html)

        return raw_html[
            start:end
        ]

    return None


def remove_repeated_name(
    text,
    raw_name
):
    pattern = (
        r"^(?:"
        + re.escape(raw_name)
        + r"\s*)+"
    )

    return re.sub(
        pattern,
        "",
        text.strip(),
        flags=re.I
    ).strip()


def parse_synergy(
    raw_html,
    raw_core,
    normalized_core,
    aliases
):
    section = find_synergy_section(
        raw_html,
        raw_core
    )

    if not section:
        return [], "section_not_found"

    text = clean_text(
        section
    )

    found = []

    for raw_name, normalized in (
        aliases.items()
    ):
        if normalized == normalized_core:
            continue

        if raw_name == normalized:
            continue

        if not re.search(
            r"[A-Za-z]",
            raw_name
        ):
            continue

        match = re.search(
            re.escape(raw_name),
            text
        )

        if not match:
            continue

        found.append(
            {
                "position":
                    match.start(),

                "raw_partner":
                    raw_name,

                "partner":
                    normalized
            }
        )

    found.sort(
        key=lambda item:
            item["position"]
    )

    unique = []
    seen = set()

    for item in found:

        partner = item[
            "partner"
        ]

        if partner in seen:
            continue

        seen.add(
            partner
        )

        unique.append(
            item
        )

    relations = []

    for index, item in enumerate(
        unique
    ):
        start = item[
            "position"
        ]

        if index + 1 < len(unique):
            end = unique[
                index + 1
            ]["position"]
        else:
            end = len(text)

        reason = text[
            start:end
        ]

        reason = remove_repeated_name(
            reason,
            item["raw_partner"]
        )

        relations.append(
            {
                "core":
                    normalized_core,

                "partner":
                    item["partner"],

                "raw_partner":
                    item["raw_partner"],

                "source_reason":
                    reason
            }
        )

    return relations, None


def main():
    pages = json.loads(
        PAGES_FILE.read_text(
            encoding="utf-8"
        )
    )["pages"]

    aliases = json.loads(
        ALIASES_FILE.read_text(
            encoding="utf-8"
        )
    )["aliases"]

    relations = []
    failed_pages = []
    empty_reason_count = 0

    for index, page in enumerate(
        pages,
        start=1
    ):
        raw_core = page[
            "raw_name"
        ]

        core = page[
            "normalized_name"
        ]

        url = page[
            "team_url"
        ]

        print(
            f"[{index}/{len(pages)}] "
            f"{core}"
        )

        try:
            status, raw = fetch(
                url
            )

            items, error = (
                parse_synergy(
                    raw,
                    raw_core,
                    core,
                    aliases
                )
            )

            if error:
                failed_pages.append(
                    {
                        "core":
                            core,

                        "url":
                            url,

                        "error":
                            error
                    }
                )

            for item in items:

                if not item.get(
                    "source_reason"
                ):
                    empty_reason_count += 1

                relations.append(
                    {
                        **item,

                        "url":
                            url,

                        "http_status":
                            status
                    }
                )

        except Exception as exc:

            failed_pages.append(
                {
                    "core":
                        core,

                    "url":
                        url,

                    "error":
                        str(exc)
                }
            )

        time.sleep(
            0.2
        )

    data = {
        "schema": 1,

        "source":
            "icyveins",

        "fetched_at":
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

        "page_count":
            len(pages),

        "relation_count":
            len(relations),

        "failed_page_count":
            len(failed_pages),

        "empty_reason_count":
            empty_reason_count,

        "failed_pages":
            failed_pages,

        "relations":
            relations
    }

    OUTPUT.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        f"Pages: {len(pages)}"
    )

    print(
        f"Relations: "
        f"{len(relations)}"
    )

    print(
        f"Failed pages: "
        f"{len(failed_pages)}"
    )

    print(
        f"Empty reasons: "
        f"{empty_reason_count}"
    )


if __name__ == "__main__":
    main()
