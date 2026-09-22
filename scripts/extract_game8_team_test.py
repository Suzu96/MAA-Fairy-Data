import json
import re
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


URL = "https://game8.jp/zenless/614253"

ALIASES_FILE = Path("data/name_aliases.json")
OUTPUT = Path("data/sources/game8_team_test.json")


def clean_text(raw_html: str) -> str:
    text = re.sub(
        r"<script[\s\S]*?</script>",
        " ",
        raw_html,
        flags=re.I
    )

    text = re.sub(
        r"<style[\s\S]*?</style>",
        " ",
        text,
        flags=re.I
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = html.unescape(text)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def load_aliases():
    data = json.loads(
        ALIASES_FILE.read_text(
            encoding="utf-8"
        )
    )

    return data["aliases"]


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

    text = clean_text(raw)

    start_marker = "星見雅編成"
    end_marker = "立ち回り例"

    start = text.find(start_marker)

    section = ""

    if start != -1:
        after_start = text[
            start + len(start_marker):
        ]

        end = after_start.find(end_marker)

        if end != -1:
            section = after_start[:end]
        else:
            section = after_start[:500]

    matches = []

    for raw_name, standard_name in aliases.items():

        pos = section.find(raw_name)

        if pos != -1:
            matches.append(
                (
                    pos,
                    raw_name,
                    standard_name
                )
            )

    matches.sort(
        key=lambda item: item[0]
    )

    raw_members = []
    normalized_members = []

    for _, raw_name, standard_name in matches:

        if standard_name in normalized_members:
            continue

        raw_members.append(raw_name)
        normalized_members.append(
            standard_name
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

        "section": start_marker,

        "raw_members": raw_members,

        "normalized_members":
            normalized_members,

        "valid_three_member_team":
            len(normalized_members) == 3
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
