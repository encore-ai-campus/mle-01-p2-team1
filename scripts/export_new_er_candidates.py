import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "data/processed/03_er/festival_scoped/er_candidates.json"
OLD_REVIEW = Path(r"C:/Users/Playdata/.codex/attachments/8fecb6d3-7f9a-4e11-ae21-c4be31b8bb49/pasted-text.txt")
OUTPUT = ROOT / "data/processed/03_er/gold/new_candidates_for_review.csv"


def pair_key(row):
    names = sorted((row.get("left_name", ""), row.get("right_name", "")))
    return (row.get("entity_type", ""), *names)


def main():
    old = set()
    with OLD_REVIEW.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            old.add(pair_key(row))
    candidates = json.loads(CURRENT.read_text(encoding="utf-8"))
    fields = ["candidate_id", "candidate_type", "entity_type", "left_entity_id", "left_name", "right_entity_id", "right_name", "similarity", "embedding_similarity", "system_decision", "human_decision", "reviewer", "review_note"]
    new_rows = []
    for index, row in enumerate(candidates, 1):
        if row.get("decision") != "review" or pair_key(row) in old:
            continue
        new_rows.append({
            "candidate_id": f"new_review_{index:04d}",
            "candidate_type": row.get("candidate_type", "fuzzy"),
            "entity_type": row.get("entity_type", ""),
            "left_entity_id": row.get("left_entity_id", ""),
            "left_name": row.get("left_name", ""),
            "right_entity_id": row.get("right_entity_id", ""),
            "right_name": row.get("right_name", ""),
            "similarity": row.get("similarity", ""),
            "embedding_similarity": row.get("embedding_similarity", ""),
            "system_decision": row.get("decision", "review"),
            "human_decision": "",
            "reviewer": "",
            "review_note": "",
        })
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(new_rows)
    print(f"new candidates: {len(new_rows)}")


if __name__ == "__main__":
    main()
