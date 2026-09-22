import json
import re
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


URL = "https://game8.jp/zenless/614253"

OUTPUT = Path("data/sources/game8_smoke.json")
ALIASES_FILE = Path("data/name_aliases.json")


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


def load_aliases():
    data = json.loads(
        ALIASES_FILE.read_text(encoding="utf-8")
    )
    return data["aliases"]


def main():
    aliases = load_aliases()

    request = Request(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/153 Safari/537.36"
            ),
            "Accept-Language": "ja,en;q=0.8"
        }
    )

    with urlopen(request, timeout=30) as response:
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

    updated_match = re.search(
        r"最終更新日[:：]?\s*"
        r"(\d{4}\.\d{2}\.\d{2}"
        r"(?:\s+\d{2}:\d{2})?)",
        text
    )

    page_updated = (
        updated_match.group(1)
        if updated_match
        else None
    )

    matched_aliases = []

    for alias, standard_name in aliases.items():
        if alias in text:
            matched_aliases.append(
                {
                    "raw": alias,
                    "normalized": standard_name
                }
            )

    normalized_characters = sorted(
        {
            item["normalized"]
            for item in matched_aliases
        }
    )

    data = {
        "schema": 1,
        "source": "game8",
        "url": URL,
        "http_status": status,
        "fetched_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "title": title,
        "page_updated": page_updated,
        "matched_aliases": matched_aliases,
        "normalized_characters": normalized_characters
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
