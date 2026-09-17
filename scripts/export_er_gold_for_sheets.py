"""Export the ER gold-pair draft as Google Sheets-ready CSV tables."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/er_gold_pairs.json"
OUT = ROOT / "data/processed/v2"


def main() -> None:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    pair_fields = [
        "pair_id", "label", "expected_decision", "candidate_type", "entity_type",
        "similarity", "left_name", "left_source_doc_id", "left_evidence",
        "right_name", "right_source_doc_id", "right_evidence",
        "human_decision", "reviewer", "review_note",
    ]
    with (OUT / "er_gold_pairs_for_sheets.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pair_fields)
        writer.writeheader()
        for pair in data["pairs"]:
            left, right = pair["left"], pair["right"]
            writer.writerow({
                "pair_id": pair["pair_id"],
                "label": pair["label"],
                "expected_decision": pair["expected_decision"],
                "candidate_type": pair["candidate_type"],
                "entity_type": pair["entity_type"],
                "similarity": pair.get("similarity", ""),
                "left_name": left["name"],
                "left_source_doc_id": left.get("source_doc_id", ""),
                "left_evidence": left.get("evidence", ""),
                "right_name": right["name"],
                "right_source_doc_id": right.get("source_doc_id", ""),
                "right_evidence": right.get("evidence", ""),
                "human_decision": "",
                "reviewer": "",
                "review_note": "",
            })

    summary_fields = ["metric", "value", "calculation_or_note"]
    summary = [
        ("Gold pair count", len(data["pairs"]), "30 positive + 10 trap"),
        ("Approved merge count", "", "Count human_decision = approved_merge"),
        ("Rejected merge count", "", "Count human_decision = rejected_merge"),
        ("Merge precision", "", "Approved merge / (approved merge + rejected merge)"),
        ("Expected positive count", data["positive_count"], "Expected merge pairs"),
        ("Expected trap count", data["trap_count"], "Expected separate pairs"),
        ("Correct decision count", "", "Approved positive + rejected trap"),
        ("Gold-set accuracy", "", "Correct decision count / Gold pair count"),
    ]
    with (OUT / "er_evaluation_template_for_sheets.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(summary_fields)
        writer.writerows(summary)

    candidates_path = OUT / "er" / "er_candidates.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    review_fields = [
        "candidate_id", "candidate_type", "entity_type", "left_entity_id",
        "left_name", "right_entity_id", "right_name", "string_similarity",
        "embedding_similarity", "system_decision", "human_decision", "reviewer",
        "review_note",
    ]
    with (OUT / "er_candidates_review_for_sheets.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=review_fields)
        writer.writeheader()
        review_index = 1
        for candidate in candidates:
            if candidate.get("decision") != "review":
                continue
            writer.writerow({
                "candidate_id": f"review_{review_index:04d}",
                "candidate_type": candidate.get("candidate_type", "fuzzy"),
                "entity_type": candidate.get("entity_type", ""),
                "left_entity_id": candidate.get("left_entity_id", ""),
                "left_name": candidate.get("left_name", ""),
                "right_entity_id": candidate.get("right_entity_id", ""),
                "right_name": candidate.get("right_name", ""),
                "string_similarity": candidate.get("similarity", ""),
                "embedding_similarity": candidate.get("embedding_similarity", ""),
                "system_decision": candidate.get("decision", ""),
                "human_decision": "",
                "reviewer": "",
                "review_note": "",
            })
            review_index += 1

    print("created Google Sheets CSV templates")


if __name__ == "__main__":
    main()
