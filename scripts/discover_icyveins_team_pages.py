import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
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


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "a":
            href = attrs.get("href")

            if href:
                self.current = {
                    "href": href,
                    "text": [],
                    "alts": []
                }

        elif (
            tag == "img"
            and self.current is not None
        ):
            alt = attrs.get("alt")

            if alt:
                self.current[
                    "alts"
                ].append(
                    alt.strip()
                )

    def handle_data(self, data):
        if self.current is None:
            return

        value = data.strip()

        if value:
            self.current[
                "text"
            ].append(
                value
            )

    def handle_endtag(self, tag):
        if (
            tag == "a"
            and self.current is not None
        ):
            self.links.append(
                self.current
            )

            self.current = None


def clean_value(value):
    return " ".join(
        value.split()
    ).strip()


def choose_name(link):
    visible = clean_value(
        " ".join(
            link["text"]
        )
    )

    if visible:
        return visible

    for alt in link["alts"]:
        alt = clean_value(
            alt
        )

        if alt:
            return alt

    return ""


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

    parser = LinkParser()
    parser.feed(raw)

    pages = []
    seen = set()

    for link in parser.links:

        href = link["href"]

        if (
            "-profile-skills-mindscapes"
            not in href
        ):
            continue

        full_url = urljoin(
            INDEX_URL,
            href
        )

        marker = (
            "/zenless-zone-zero/"
        )

        if marker not in full_url:
            continue

        slug_part = full_url.split(
            marker,
            1
        )[1]

        slug = slug_part.split(
            "-profile-skills-mindscapes",
            1
        )[0]

        if not slug:
            continue

        if slug in seen:
            continue

        seen.add(
            slug
        )

        raw_name = choose_name(
            link
        )

        normalized_name = (
            aliases.get(
                raw_name
            )
            if raw_name
            else None
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
                    full_url,

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
            if (
                item["raw_name"]
                and not item[
                    "normalized_name"
                ]
            )
        }
    )

    mapped_count = sum(
        1
        for item in pages
        if item[
            "normalized_name"
        ]
    )

    data = {
        "schema": 4,

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

        "mapped_name_count":
            mapped_count,

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
