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


def make_team(group, indexes):
    raw_members = [
        group[i]["raw"]
        for i in indexes
    ]

    members = [
        group[i]["normalized"]
        for i in indexes
    ]

    return {
        "raw_members":
            raw_members,

        "normalized_members":
            members,

        "fully_normalized":
            (
                len(members) == 3
                and all(members)
            )
    }


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

    core_indexes = [
        index
        for index, anchor
        in enumerate(anchors)
        if anchor["normalized"]
        == normalized_core
    ]

    teams = []
    warnings = []

    for group_number, start_index in enumerate(
        core_indexes
    ):
        if (
            group_number + 1
            < len(core_indexes)
        ):
            end_index = core_indexes[
                group_number + 1
            ]
        else:
            end_index = len(anchors)

        group = anchors[
            start_index:end_index
        ]

        unique_group = []
        seen = set()

        for anchor in group:
            name = anchor[
                "normalized"
            ]

            if name in seen:
                continue

            seen.add(name)
            unique_group.append(
                anchor
            )

        group = unique_group

        if len(group) == 3:
            teams.append(
                make_team(
                    group,
                    [0, 1, 2]
                )
            )
            continue

        if len(group) == 4:
            between = section_html[
                group[2]["end"]:
                group[3]["start"]
            ]

            between_text = clean_html(
                between
            )

            if "/" in between_text:
                teams.append(
                    make_team(
                        group,
                        [0, 1, 2]
                    )
                )

                teams.append(
                    make_team(
                        group,
                        [0, 1, 3]
                    )
                )

                continue

        if group:
            warnings.append(
                {
                    "type":
                        "unexpected_group",

                    "raw_group":
                        [
                            item["raw"]
                            for item in group
                        ],

                    "normalized_group":
                        [
                            item["normalized"]
                            for item in group
                        ]
                }
            )

    deduped = []
    seen_keys = set()

    for team in teams:
        key = tuple(
            sorted(
                team[
                    "normalized_members"
                ]
            )
        )

        if key in seen_keys:
            continue

        seen_keys.add(key)
        deduped.append(team)

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
