import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


INPUT = Path(
    "data/sources/icyveins_team_pages.json"
)

OUTPUT = Path(
    "data/sources/icyveins_team_page_status.json"
)


def check_url(url):
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

    try:
        with urlopen(
            request,
            timeout=20
        ) as response:

            return {
                "status":
                    response.status,

                "final_url":
                    response.geturl()
            }

    except HTTPError as exc:
        return {
            "status":
                exc.code,

            "final_url":
                url,

            "error":
                str(exc)
        }

    except URLError as exc:
        return {
            "status":
                None,

            "final_url":
                url,

            "error":
                str(exc)
        }

    except Exception as exc:
        return {
            "status":
                None,

            "final_url":
                url,

            "error":
                str(exc)
        }


def main():
    source = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

    results = []

    for index, page in enumerate(
        source.get(
            "pages",
            []
        ),
        start=1
    ):
        name = page[
            "normalized_name"
        ]

        url = page[
            "team_url"
        ]

        print(
            f"[{index}/"
            f"{source['page_count']}] "
            f"{name}"
        )

        result = check_url(
            url
        )

        results.append(
            {
                "character":
                    name,

                "raw_name":
                    page["raw_name"],

                "slug":
                    page["slug"],

                "team_url":
                    url,

                **result
            }
        )

        time.sleep(
            0.15
        )

    ok_count = sum(
        1
        for item in results
        if item.get("status") == 200
    )

    failed = [
        item
        for item in results
        if item.get("status") != 200
    ]

    data = {
        "schema": 1,

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
            len(results),

        "ok_count":
            ok_count,

        "failed_count":
            len(failed),

        "failed_pages":
            failed,

        "pages":
            results
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
        f"OK: {ok_count}"
    )

    print(
        f"Failed: {len(failed)}"
    )


if __name__ == "__main__":
    main()
