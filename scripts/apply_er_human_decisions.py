import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "data/processed/03_er/festival_scoped"
OLD_REVIEW = Path(r"C:/Users/Playdata/.codex/attachments/8fecb6d3-7f9a-4e11-ae21-c4be31b8bb49/pasted-text.txt")
NEW_REVIEW = ROOT / "data/processed/03_er/gold/new_candidates_for_review.csv"
OUTPUT = ROOT / "data/processed/03_er/final"


def key(entity_type, left, right):
    return (entity_type, *sorted((left, right)))


def load_decisions():
    decisions = {}
    with OLD_REVIEW.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            decision = row.get("human_decision", "").strip().lower()
            if decision:
                decisions[key(row["entity_type"], row["left_name"], row["right_name"])] = decision
    with NEW_REVIEW.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            decisions[key(row["entity_type"], row["left_name"], row["right_name"])] = "approved_merge"
    return decisions


def main():
    entities = json.loads((CURRENT / "resolved_entities.json").read_text(encoding="utf-8"))
    triples = json.loads((CURRENT / "resolved_triples.json").read_text(encoding="utf-8"))
    candidates = json.loads((CURRENT / "er_candidates.json").read_text(encoding="utf-8"))
    decisions = load_decisions()
    by_name = {(e["entity_type"], e["canonical_name"], e.get("parent_festival_id")): i for i, e in enumerate(entities)}
    parent = list(range(len(entities)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for candidate in candidates:
        decision = decisions.get(key(candidate.get("entity_type", ""), candidate.get("left_name", ""), candidate.get("right_name", "")))
        if decision not in {"merge", "approved_merge"}:
            continue
        left = next((i for i, e in enumerate(entities) if e["entity_id"] == candidate.get("left_entity_id")), None)
        right = next((i for i, e in enumerate(entities) if e["entity_id"] == candidate.get("right_entity_id")), None)
        if left is not None and right is not None and entities[left].get("entity_type") == entities[right].get("entity_type"):
            if entities[left].get("entity_type") != "Program" or entities[left].get("parent_festival_id") == entities[right].get("parent_festival_id"):
                parent[find(right)] = find(left)

    groups = defaultdict(list)
    for i in range(len(entities)):
        groups[find(i)].append(entities[i])
    old_to_new = {}
    merged = []
    for new_index, members in enumerate(groups.values()):
        base = dict(members[0])
        new_id = f"entity_{new_index}"
        base["entity_id"] = new_id
        base["mention_ids"] = [m for e in members for m in e.get("mention_ids", [])]
        base["source_doc_ids"] = list(dict.fromkeys(d for e in members for d in e.get("source_doc_ids", [])))
        base["source_mentions"] = [m for e in members for m in e.get("source_mentions", [])]
        merged.append(base)
        for e in members:
            old_to_new[e["entity_id"]] = new_id

    report = {
        "entity_count_before": len(entities),
        "entity_count_after": len(merged),
        "merged_entity_count": len(entities) - len(merged),
        "approved_merge_count": sum(v in {"merge", "approved_merge"} for v in decisions.values()),
        "rejected_merge_count": sum(v in {"separate", "rejected_merge"} for v in decisions.values()),
        "decision_count": len(decisions),
    }
    # Rewrite triple endpoint names using the final canonical entity mapping.
    endpoint_map = defaultdict(set)
    for entity in merged:
        for mention in entity.get("source_mentions", []):
            endpoint_map[(entity["entity_type"], mention.get("name"))].add(entity["canonical_name"])
    resolved_triples = []
    for triple in triples:
        row = dict(triple)
        for role in ("subject", "object"):
            options = endpoint_map.get((row.get(f"{role}_type"), row.get(role)), set())
            if len(options) == 1:
                row[role] = next(iter(options))
        resolved_triples.append(row)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, value in {
        "resolved_entities.json": merged,
        "resolved_triples.json": resolved_triples,
        "er_candidates.json": candidates,
        "er_report.json": report,
    }.items():
        (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
