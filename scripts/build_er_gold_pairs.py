"""Build a reviewable ER gold-pair draft from pre-ER clean triples."""

import json
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.entity_resolution.er import normalize_comparison_name


INPUT = ROOT / "data/processed/03_er/input/triples_clean_v2.json"
OUTPUT = ROOT / "data/processed/03_er/gold/er_gold_pairs_v1.json"


def main() -> None:
    rows = json.loads(INPUT.read_text(encoding="utf-8"))
    mentions = defaultdict(list)
    for item in rows:
        triple = item.get("triple", item)
        for role in ("subject", "object"):
            name = triple.get(role)
            entity_type = triple.get(f"{role}_type")
            if name and entity_type:
                key = (entity_type, name)
                if not mentions[key]:
                    mentions[key].append({
                        "name": name,
                        "entity_type": entity_type,
                        "source_doc_id": triple.get("source_doc_id"),
                        "evidence": triple.get("evidence"),
                    })

    by_normalized = defaultdict(list)
    for (entity_type, name), samples in mentions.items():
        by_normalized[(entity_type, normalize_comparison_name(name))].append(samples[0])

    pairs = []
    seen = set()
    positive_count = 0

    # Positive pairs: distinct original strings with the same type and normalized name.
    for (entity_type, normalized), values in by_normalized.items():
        for left_index, left in enumerate(values):
            for right in values[left_index + 1:]:
                if left["name"] == right["name"]:
                    continue
                pair = (entity_type, left["name"], right["name"])
                if pair in seen:
                    continue
                seen.add(pair)
                pairs.append({
                    "pair_id": f"gold_{len(pairs) + 1:03d}",
                    "label": "positive",
                    "expected_decision": "merge",
                    "candidate_type": "exact_normalized",
                    "entity_type": entity_type,
                    "left": left,
                    "right": right,
                    "review_status": "needs_human_confirmation",
                })
                positive_count += 1
                if positive_count >= 30:
                    break
            if positive_count >= 30:
                break
        if positive_count >= 30:
            break

    # Negative traps: high lexical similarity, but different normalized names.
    by_type = defaultdict(list)
    for (entity_type, name), samples in mentions.items():
        by_type[entity_type].append(samples[0])
    traps = []
    for entity_type, values in by_type.items():
        blocks = defaultdict(list)
        for value in values:
            normalized = normalize_comparison_name(value["name"])
            blocks[(normalized[:2], len(normalized) // 3)].append(value)
        for block in blocks.values():
            for left_index, left in enumerate(block):
                for right in block[left_index + 1:]:
                    if normalize_comparison_name(left["name"]) == normalize_comparison_name(right["name"]):
                        continue
                    score = SequenceMatcher(None, normalize_comparison_name(left["name"]), normalize_comparison_name(right["name"])).ratio()
                    if 0.72 <= score < 0.98:
                        traps.append((score, entity_type, left, right))
    for score, entity_type, left, right in sorted(traps, key=lambda item: item[0], reverse=True)[:10]:
        pairs.append({
            "pair_id": f"gold_{len(pairs) + 1:03d}",
            "label": "trap",
            "expected_decision": "separate",
            "candidate_type": "fuzzy_trap",
            "entity_type": entity_type,
            "similarity": round(score, 4),
            "left": left,
            "right": right,
            "review_status": "needs_human_confirmation",
        })

    result = {
        "version": "v1",
        "input": str(INPUT.relative_to(ROOT)),
        "description": "Draft only. Human confirmation is required before using as ER gold data.",
        "positive_count": sum(p["label"] == "positive" for p in pairs),
        "trap_count": sum(p["label"] == "trap" for p in pairs),
        "pairs": pairs,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"created {OUTPUT} ({len(pairs)} pairs)")


if __name__ == "__main__":
    main()
