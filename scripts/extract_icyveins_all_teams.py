import json
import re
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


URL = (
    "https://www.icy-veins.com/"
    "zenless-zone-zero/hoshimi-miyabi-teams"
)

ALIASES_FILE = Path("data/name_aliases.json")

OUTPUT = Path(
    "data/sources/icyveins_all_teams.json"
)


def clean_html(value: str) -> str:
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


def load_aliases():
    data = json.loads(
        ALIASES_FILE.read_text(
            encoding="utf-8"
        )
    )

    return data["aliases"]


def find_best_teams_section(raw_html):
    headings = list(
        re.finditer(
            r"<h2\b[^>]*>(.*?)</h2>",
            raw_html,
            flags=re.I | re.S
        )
    )

    for index, match in enumerate(headings):

        heading = clean_html(
            match.group(1)
        )

        if heading != "Hoshimi Miyabi's Best Teams":
            continue

        start = match.end()

        if index + 1 < len(headings):
            end = headings[
                index + 1
            ].start()
        else:
            end = len(raw_html)

        return raw_html[start:end]

    raise RuntimeError(
        "Best Teams section not found."
    )


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

        if raw_name not in aliases:
            continue

        anchors.append(
            {
                "start": match.start(),
                "end": match.end(),
                "raw": raw_name,
                "normalized":
                    aliases[raw_name]
            }
        )

    return anchors


def make_team(
    anchor_group,
    indexes
):
    raw_members = [
        anchor_group[i]["raw"]
        for i in indexes
    ]

    members = [
        anchor_group[i]["normalized"]
        for i in indexes
    ]

    return {
        "raw_members": raw_members,
        "normalized_members": members,
        "fully_normalized": (
            len(members) == 3
            and all(members)
        )
    }


def main():
    aliases = load_aliases()

    request = Request(
        URL,
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

        status = response.status

        raw = response.read().decode(
            "utf-8",
            errors="replace"
        )

    section_html = (
        find_best_teams_section(raw)
    )

    anchors = extract_character_anchors(
        section_html,
        aliases
    )

    core_name = "星见雅"

    core_indexes = [
        index
        for index, anchor
        in enumerate(anchors)
        if anchor["normalized"]
        == core_name
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
        seen_names = set()

        for anchor in group:

            name = anchor["normalized"]

            if name in seen_names:
                continue

            seen_names.add(name)
            unique_group.append(anchor)

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

            between_text = html.unescape(
                clean_html(between)
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

        warnings.append(
            {
                "raw_group": [
                    item["raw"]
                    for item in group
                ],
                "normalized_group": [
                    item["normalized"]
                    for item in group
                ]
            }
        )

    deduped = []
    seen_team_keys = set()

    for team in teams:

        members = team[
            "normalized_members"
        ]

        key = tuple(
            sorted(members)
        )

        if key in seen_team_keys:
            continue

        seen_team_keys.add(key)

        deduped.append(team)

    data = {
        "schema": 1,
        "source": "icyveins",
        "url": URL,
        "http_status": status,

        "fetched_at": datetime.now(
            timezone.utc
        )
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),

        "core": "星见雅",

        "team_count": len(deduped),

        "teams": deduped,

        "warnings": warnings
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
