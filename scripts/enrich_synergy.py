import json
from pathlib import Path


FILE = Path("data/synergy.json")


TAG_RULES = [
    ("polarity disorder", "极性紊乱"),
    ("disorder", "紊乱"),
    ("anomaly buildup", "异常积蓄"),
    ("anomaly", "异常"),
    ("stun", "失衡"),
    ("ice dmg", "冰伤"),
    ("res shred", "抗性削减"),
    ("atk", "攻击增益"),
    ("crit dmg", "暴击伤害"),
    ("crit rate", "暴击率"),
    ("fallen frost", "落霜"),
    ("ultimate", "终结技"),
    ("quick assist", "快速支援"),
    ("chain attack", "连携技"),
    ("off-field", "后台输出"),
    ("sub dps", "副C"),
    ("support", "支援")
]


def detect_tags(text):
    text_lower = text.lower()

    tags = []

    for keyword, tag in TAG_RULES:
        if keyword in text_lower:
            if tag not in tags:
                tags.append(tag)

    return tags


def main():
    data = json.loads(
        FILE.read_text(
            encoding="utf-8"
        )
    )

    tagged_count = 0

    for relation in data.get(
        "relations",
        []
    ):
        evidence_type = relation.get(
            "evidence_type"
        )

        if evidence_type == "explicit_reason":

            source_reason = (
                relation.get(
                    "source_reason"
                )
                or ""
            )

            tags = detect_tags(
                source_reason
            )

            relation["tags"] = tags

            if tags:
                relation["reason_zh"] = (
                    f"{relation['partner']}的主要协同方向："
                    + "、".join(tags)
                    + "。"
                )
            else:
                relation["reason_zh"] = (
                    f"{relation['partner']}与"
                    f"{relation['core']}存在明确攻略协同。"
                )

            tagged_count += 1

        else:
            relation["tags"] = (
                relation.get("tags")
                or []
            )

            if not relation.get(
                "reason_zh"
            ):
                relation["reason_zh"] = (
                    f"Icy Veins 将"
                    f"{relation['partner']}列为"
                    f"{relation['core']}的推荐搭档。"
                )

    data["schema"] = 5

    data[
        "enriched_explicit_count"
    ] = tagged_count

    FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        "Enriched explicit relations:",
        tagged_count
    )


if __name__ == "__main__":
    main()
