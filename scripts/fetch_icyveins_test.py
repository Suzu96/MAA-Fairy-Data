import json
import re
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


URL = "https://www.icy-veins.com/zenless-zone-zero/hoshimi-miyabi-teams"

OUTPUT = Path("data/sources/icyveins_smoke.json")


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

    text = re.sub(r"<[^>]+>", " ", text)

    text = html.unescape(text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def main():
    request = Request(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/153 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
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

    title_match = re.search(
        r"<title[^>]*>(.*?)</title>",
        raw,
        flags=re.I | re.S
    )

    title = ""

    if title_match:
        title = html.unescape(
            re.sub(
                r"\s+",
                " ",
                title_match.group(1)
            )
        ).strip()

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

        "title": title,

        "checks": {
            "has_miyabi":
                "Hoshimi Miyabi" in text,

            "has_nangong_yu":
                "Nangong Yu" in text,

            "has_yuzuha":
                "Ukinami Yuzuha" in text,

            "has_yanagi":
                "Tsukishiro Yanagi" in text,

            "has_best_teams_section":
                "Best Teams" in text
        }
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
