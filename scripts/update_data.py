import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    output = Path("data/automation_test.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "status": "ok",
        "message": "MAA-Fairy automatic data update test"
    }

    output.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(f"Generated: {output}")
    print(f"Time: {data['generated_at']}")


if __name__ == "__main__":
    main()
