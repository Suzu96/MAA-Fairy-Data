import json
from pathlib import Path


FILE = Path("data/synergy.json")


TAG_RULES = [
    ("disorder", "紊乱"),
    ("polarity disorder", "极性紊乱"),
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


def build_reason(partner, tags):
    if not tags:
        return f"{partner}与核心角色存在攻略推荐协同。"

    return (
        f"{partner}的主要协同方向："
        + "、".join(tags)
        + "。"
    )


def main():
    data = json.loads(
        FILE.read_text(
            encoding="utf-8"
        )
    )

    for relation in data.get(
        "relations",
        []
    ):
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

        relation["reason_zh"] = build_reason(
            relation["partner"],
            tags
        )

    data["schema"] = 3

    FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print(
        "Synergy enrichment complete."
    )


if __name__ == "__main__":
    main()
