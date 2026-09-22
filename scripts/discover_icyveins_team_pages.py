import json
import re
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


INDEX_URL = (
    "https://www.icy-veins.com/"
    "zenless-zone-zero/agents"
)

ALIASES_FILE = Path(
    "data/name_aliases.json"
)

OUTPUT = Path(
    "data/sources/icyveins_team_pages.json"
)


def clean_text(value):
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


def main():
    aliases = json.loads(
        ALIASES_FILE.read_text(
            encoding="utf-8"
        )
    )["aliases"]

    request = Request(
        INDEX_URL,
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

    pattern = re.compile(
        r'<a\b[^>]*href=["\']'
        r'(?:https://www\.icy-veins\.com)?'
        r'(/zenless-zone-zero/'
        r'([a-z0-9-]+)'
        r'-profile-skills-mindscapes)'
        r'(?:[?#][^"\']*)?'
        r'["\'][^>]*>'
        r'(.*?)'
        r'</a>',
        flags=re.I | re.S
    )

    pages = []
    seen = set()

    for match in pattern.finditer(raw):

        profile_path = match.group(1)
        slug = match.group(2)

        raw_name = clean_text(
            match.group(3)
        )

        if slug in seen:
            continue

        if not raw_name:
            continue

        seen.add(slug)

        normalized_name = (
            aliases.get(raw_name)
        )

        pages.append(
            {
                "raw_name":
                    raw_name,

                "normalized_name":
                    normalized_name,

                "slug":
                    slug,

                "profile_url":
                    (
                        "https://www.icy-veins.com"
                        + profile_path
                    ),

                "team_url":
                    (
                        "https://www.icy-veins.com/"
                        "zenless-zone-zero/"
                        + slug
                        + "-teams"
                    )
            }
        )

    pages.sort(
        key=lambda item:
            item["raw_name"].lower()
    )

    unmapped = sorted(
        {
            item["raw_name"]
            for item in pages
            if not item[
                "normalized_name"
            ]
        }
    )

    data = {
        "schema": 2,

        "source":
            "icyveins",

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

        "page_count":
            len(pages),

        "unmapped_name_count":
            len(unmapped),

        "unmapped_names":
            unmapped,

        "pages":
            pages
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
