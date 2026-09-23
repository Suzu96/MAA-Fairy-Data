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
    "data/sources/icyveins_all_character_teams.json"
)


def clean_html(value):
    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = html.unescape(value)

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


def find_best_teams_section(
    raw_html,
    raw_name
):
    headings = list(
        re.finditer(
            r"<h2\b[^>]*>(.*?)</h2>",
            raw_html,
            flags=re.I | re.S
        )
    )

    candidates = [
        f"{raw_name}'s Best Teams",
        f"{raw_name} Best Teams"
    ]

    for index, match in enumerate(
        headings
    ):
        heading = clean_html(
            match.group(1)
        )

        if heading not in candidates:
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


def extract_character_anchors(
    section_html,
    aliases
):
    anchors = []

    for match in re.finditer(
        r"<a\b[^>]*>(.*?)</a>",
        section_html,
        flags=re.I | re.S
    ):
        raw_name = clean_html(
            match.group(1)
        )

        normalized = aliases.get(
            raw_name
        )

        if not normalized:
            continue

        anchors.append(
            {
                "start":
                    match.start(),

                "end":
                    match.end(),

                "raw":
                    raw_name,

                "normalized":
                    normalized
            }
        )

    return anchors


def build_team(group):
    return {
        "raw_members": [
            item["raw"]
            for item in group
        ],

        "normalized_members": [
            item["normalized"]
            for item in group
        ],

        "fully_normalized": True
    }


def has_slash_between(
    section_html,
    left,
    right
):
    between = section_html[
        left["end"]:
        right["start"]
    ]

    text = clean_html(
        between
    )

    return "/" in text


def parse_page(
    raw_html,
    raw_core,
    normalized_core,
    aliases
):
    section_html = (
        find_best_teams_section(
            raw_html,
            raw_core
        )
    )

    if not section_html:
        return [], [
            {
                "type":
                    "best_teams_section_not_found"
            }
        ]

    anchors = extract_character_anchors(
        section_html,
        aliases
    )

    teams = []
    warnings = []

    i = 0

    while i < len(anchors):

        remaining = len(anchors) - i

        if remaining < 3:
            break

        # First check whether the next 4 names
        # represent a 3-person team with
        # one alternative slot.
        if remaining >= 4:

            group4 = anchors[
                i:i + 4
            ]

            alt_pair = None

            for j in range(3):

                if has_slash_between(
                    section_html,
                    group4[j],
                    group4[j + 1]
                ):
                    alt_pair = (
                        j,
                        j + 1
                    )
                    break

            if alt_pair is not None:

                left_alt, right_alt = (
                    alt_pair
                )

                team_a = [
                    item
                    for index, item
                    in enumerate(group4)
                    if index != right_alt
                ]

                team_b = [
                    item
                    for index, item
                    in enumerate(group4)
                    if index != left_alt
                ]

                members_a = [
                    item["normalized"]
                    for item in team_a
                ]

                members_b = [
                    item["normalized"]
                    for item in team_b
                ]

                if (
                    normalized_core
                    in members_a
                    and normalized_core
                    in members_b
                ):
                    teams.append(
                        build_team(
                            team_a
                        )
                    )

                    teams.append(
                        build_team(
                            team_b
                        )
                    )

                    i += 4
                    continue

        # Normal team: three consecutive agents.
        group3 = anchors[
            i:i + 3
        ]

        members = [
            item["normalized"]
            for item in group3
        ]

        if normalized_core in members:

            teams.append(
                build_team(
                    group3
                )
            )

            i += 3
            continue

        # Something unexpected appeared.
        # Skip one anchor and try to recover.
        warnings.append(
            {
                "type":
                    "unmatched_sequence",

                "raw_group":
                    [
                        item["raw"]
                        for item in group3
                    ],

                "normalized_group":
                    members
            }
        )

        i += 1

    deduped = []
    seen_keys = set()

    for team in teams:

        members = team[
            "normalized_members"
        ]

        key = tuple(
            sorted(members)
        )

        if key in seen_keys:
            continue

        seen_keys.add(
            key
        )

        deduped.append(
            team
        )

    return deduped, warnings


def main():
    pages_data = json.loads(
        PAGES_FILE.read_text(
            encoding="utf-8"
        )
    )

    aliases = json.loads(
        ALIASES_FILE.read_text(
            encoding="utf-8"
        )
    )["aliases"]

    page_results = []
    all_teams = []
    failed_pages = []

    warning_count = 0

    pages = pages_data.get(
        "pages",
        []
    )

    for index, page in enumerate(
        pages,
        start=1
    ):
        raw_core = page[
            "raw_name"
        ]

        normalized_core = page[
            "normalized_name"
        ]

        url = page[
            "team_url"
        ]

        print(
            f"[{index}/{len(pages)}] "
            f"{normalized_core}"
        )

        try:
            status, raw = fetch(
                url
            )

            teams, warnings = (
                parse_page(
                    raw,
                    raw_core,
                    normalized_core,
                    aliases
                )
            )

            warning_count += len(
                warnings
            )

            page_results.append(
                {
                    "core":
                        normalized_core,

                    "raw_core":
                        raw_core,

                    "url":
                        url,

                    "http_status":
                        status,

                    "team_count":
                        len(teams),

                    "warning_count":
                        len(warnings),

                    "warnings":
                        warnings
                }
            )

            for team in teams:

                all_teams.append(
                    {
                        "core":
                            normalized_core,

                        "raw_core":
                            raw_core,

                        "url":
                            url,

                        **team
                    }
                )

        except Exception as exc:

            failed_pages.append(
                {
                    "core":
                        normalized_core,

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
        "schema": 2,

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

        "parsed_page_count":
            len(page_results),

        "failed_page_count":
            len(failed_pages),

        "team_count":
            len(all_teams),

        "warning_count":
            warning_count,

        "failed_pages":
            failed_pages,

        "pages":
            page_results,

        "teams":
            all_teams
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
        f"Parsed: "
        f"{len(page_results)}"
    )

    print(
        f"Failed: "
        f"{len(failed_pages)}"
    )

    print(
        f"Teams: "
        f"{len(all_teams)}"
    )

    print(
        f"Warnings: "
        f"{warning_count}"
    )


if __name__ == "__main__":
    main()
