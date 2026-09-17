"""Add a conservative first-pass merge/separate proposal to the ER review CSV."""

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/03_er/gold/er_candidates_review_for_sheets.csv"
OUTPUT = INPUT


def normalized(value: str) -> str:
    return re.sub(r"[^\w\s]+", "", value.casefold()).replace(" ", "")


def propose(row: dict[str, str]) -> tuple[str, str, str]:
    left = normalized(row["left_name"])
    right = normalized(row["right_name"])
    score = float(row["string_similarity"] or 0)
    if left == right:
        return "merge", "normalized names are identical", "high"
    if score >= 0.94 and (left in right or right in left):
        return "merge", "very high similarity and one name contains the other", "medium"
    if score >= 0.90 and row["entity_type"] in {"Organization", "Location", "Theme"}:
        return "merge", "high similarity in a type commonly affected by formatting variants", "medium"
    return "separate", "not an unambiguous formatting-only variation", "medium"


def main() -> None:
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0]) + ["first_pass_decision", "first_pass_confidence", "first_pass_reason"]
    counts = {"merge": 0, "separate": 0}
    for row in rows:
        decision, reason, confidence = propose(row)
        row["first_pass_decision"] = decision
        row["first_pass_confidence"] = confidence
        row["first_pass_reason"] = reason
        counts[decision] += 1
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"updated {len(rows)} candidates: merge={counts['merge']}, separate={counts['separate']}")


if __name__ == "__main__":
    main()
