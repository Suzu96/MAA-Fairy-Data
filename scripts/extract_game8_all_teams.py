import json
import re
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


URL = "https://game8.jp/zenless/614253"

ALIASES_FILE = Path("data/name_aliases.json")
OUTPUT = Path("data/sources/game8_all_teams.json")


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def load_aliases():
    data = json.loads(
        ALIASES_FILE.read_text(
            encoding="utf-8"
        )
    )

    return data["aliases"]


def normalize_name(raw_name, aliases):
    return aliases.get(raw_name)


def extract_anchor_texts(fragment):
    names = []

    for match in re.finditer(
        r"<a\b[^>]*>(.*?)</a>",
        fragment,
        flags=re.I | re.S
    ):
        text = clean_html(match.group(1))

        if not text:
            continue

        if text.startswith("▶"):
            continue

        if text.startswith("▲"):
            continue

        if text not in names:
            names.append(text)

    return names


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
            "Accept-Language": "ja,en;q=0.8"
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

    h3_matches = list(
        re.finditer(
            r"<h3\b[^>]*>(.*?)</h3>",
            raw,
            flags=re.I | re.S
        )
    )

    teams = []
    unmapped_names = set()

    for index, heading_match in enumerate(h3_matches):

        heading = clean_html(
            heading_match.group(1)
        )

        section_start = heading_match.end()

        if index + 1 < len(h3_matches):
            section_end = h3_matches[
                index + 1
            ].start()
        else:
            section_end = len(raw)

        section_html = raw[
            section_start:section_end
        ]

        walkthrough_pos = section_html.find(
            "立ち回り例"
        )

        if walkthrough_pos == -1:
            continue

        team_area = section_html[
            :walkthrough_pos
        ]

        raw_candidates = extract_anchor_texts(
            team_area
        )

        if len(raw_candidates) < 3:
            continue

        raw_members = raw_candidates[:3]

        normalized_members = []

        for raw_name in raw_members:

            normalized = normalize_name(
                raw_name,
                aliases
            )

            if normalized:
                normalized_members.append(
                    normalized
                )
            else:
                normalized_members.append(
                    None
                )
                unmapped_names.add(
                    raw_name
                )

        teams.append(
            {
                "section": heading,
                "raw_members": raw_members,
                "normalized_members":
                    normalized_members,
                "fully_normalized":
                    all(
                        member is not None
                        for member
                        in normalized_members
                    )
            }
        )

    data = {
        "schema": 1,
        "source": "game8",
        "url": URL,
        "http_status": status,

        "fetched_at": datetime.now(
            timezone.utc
        )
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),

        "team_count": len(teams),

        "teams": teams,

        "unmapped_names": sorted(
            unmapped_names
        )
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
