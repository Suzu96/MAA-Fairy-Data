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

ALIASES_FILE = Path(
    "data/name_aliases.json"
)

OUTPUT = Path(
    "data/sources/icyveins_synergy_miyabi.json"
)


def clean_text(value: str) -> str:
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


def load_aliases():
    data = json.loads(
        ALIASES_FILE.read_text(
            encoding="utf-8"
        )
    )

    return data["aliases"]


def find_synergy_section(
    raw_html
):
    headings = list(
        re.finditer(
            r"<h2\b[^>]*>(.*?)</h2>",
            raw_html,
            flags=re.I | re.S
        )
    )

    target = (
        "Best Pairings and Synergies "
        "With Hoshimi Miyabi"
    )

    for index, match in enumerate(
        headings
    ):

        heading = clean_text(
            match.group(1)
        )

        if heading != target:
            continue

        start = match.end()

        if index + 1 < len(headings):
            end = headings[
                index + 1
            ].start()
        else:
            end = len(
                raw_html
            )

        return raw_html[
            start:end
        ]

    raise RuntimeError(
        "Synergy section not found."
    )


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
        find_synergy_section(raw)
    )

    section_text = clean_text(
        section_html
    )

    core = "星见雅"

    english_aliases = []

    for raw_name, standard_name in (
        aliases.items()
    ):

        if not raw_name:
            continue

        if raw_name == standard_name:
            continue

        if not re.search(
            r"[A-Za-z]",
            raw_name
        ):
            continue

        if raw_name not in section_text:
            continue

        if standard_name == core:
            continue

        english_aliases.append(
            (
                raw_name,
                standard_name
            )
        )

    positions = []

    for raw_name, standard_name in (
        english_aliases
    ):

        match = re.search(
            re.escape(raw_name),
            section_text
        )

        if not match:
            continue

        positions.append(
            {
                "position":
                    match.start(),

                "raw_name":
                    raw_name,

                "character":
                    standard_name
            }
        )

    positions.sort(
        key=lambda item:
            item["position"]
    )

    # Remove duplicate normalized names.
    unique = []
    seen = set()

    for item in positions:

        character = item[
            "character"
        ]

        if character in seen:
            continue

        seen.add(
            character
        )

        unique.append(
            item
        )

    synergies = []

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
            end = len(
                section_text
            )

        chunk = section_text[
            start:end
        ]

        # Remove the repeated character
        # name at the beginning.
        chunk = re.sub(
            r"^"
            + re.escape(
                item["raw_name"]
            )
            + r"\s*",
            "",
            chunk
        )

        chunk = chunk.strip()

        synergies.append(
            {
                "core":
                    core,

                "partner":
                    item["character"],

                "raw_partner":
                    item["raw_name"],

                "source_reason":
                    chunk
            }
        )

    data = {
        "schema": 1,

        "source":
            "icyveins",

        "url":
            URL,

        "http_status":
            status,

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

        "core":
            core,

        "synergy_count":
            len(
                synergies
            ),

        "synergies":
            synergies
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
