#!/usr/bin/env python3
"""Small labelled synthetic evaluation for exact, fuzzy-only and hybrid matching.

This is a reproducible demonstration fixture, not a claim of general real-world
accuracy. It evaluates against the eight canonical records in manufacturer/02_seed.sql.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rapidfuzz.fuzz import ratio
from mediator.entity_matcher import match_candidates, normalize_identifier, _code_similarity


CANDIDATES = [
    {"ItemCode": "MED1001", "ProductName": "Paracetamol 500 mg Tablet", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24P01", "ExpiryDate": "2028-01-09"},
    {"ItemCode": "MED1002", "ProductName": "Paracetamol 500 mg Tablet", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24P02", "ExpiryDate": "2028-01-11"},
    {"ItemCode": "MED1003", "ProductName": "Azithromycin 250 mg Tablet", "Manufacturer": "Bharat Health Labs", "BatchNo": "BH24A11", "ExpiryDate": "2028-02-04"},
    {"ItemCode": "MED1004", "ProductName": "Pantoprazole 40 mg Tablet", "Manufacturer": "CureNova Pharmaceuticals", "BatchNo": "CN24T09", "ExpiryDate": "2028-02-17"},
    {"ItemCode": "MED1005", "ProductName": "Cetirizine 10 mg Tablet", "Manufacturer": "Bharat Health Labs", "BatchNo": "BH24C22", "ExpiryDate": "2028-03-01"},
    {"ItemCode": "MED1006", "ProductName": "Amoxicillin 500 mg Capsule", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24M18", "ExpiryDate": "2028-03-10"},
    {"ItemCode": "MED1007", "ProductName": "ORS Powder Sachet", "Manufacturer": "CureNova Pharmaceuticals", "BatchNo": "CN24O12", "ExpiryDate": "2028-03-18"},
    {"ItemCode": "MED1008", "ProductName": "Ibuprofen 400 mg Tablet", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24I07", "ExpiryDate": "2028-03-31"},
]

CASES = [
    {"case": "exact identifier", "code": "MED1001", "name": "Paracetamol 500 mg Tablet", "batch": "AX24P01", "manufacturer": "Apex Lifesciences Pvt Ltd", "expiry": "2028-01-09", "expected": "MED1001"},
    {"case": "OCR O/0 confusion", "code": "MED1OO2", "name": "Paracetamol 500 mg Tablet", "batch": "AX24P02", "manufacturer": "Apex Lifesciences Pvt Ltd", "expiry": "2028-01-11", "expected": "MED1002"},
    {"case": "one character plus context", "code": "MED100Z", "name": "ORS Powder Sachet", "batch": "CN24O12", "manufacturer": "CureNova Pharmaceuticals", "expiry": "2028-03-18", "expected": "MED1007"},
    {"case": "product name typo", "code": "MED1006", "name": "Amoxcillin 500 mg Capsule", "batch": "AX24M18", "manufacturer": "Apex Lifesciences Pvt Ltd", "expiry": "2028-03-10", "expected": "MED1006"},
    {"case": "code conflicts with batch", "code": "MED1001", "name": "Paracetamol 500 mg Tablet", "batch": "AX24P02", "manufacturer": "Apex Lifesciences Pvt Ltd", "expiry": "2028-01-11", "expected": "MED1002"},
    {"case": "unknown medicine", "code": "MED7777", "name": "Mystery product", "batch": "ZZ99ZZ", "manufacturer": "Unknown Manufacturer", "expiry": "2029-12-31", "expected": None},
]


def as_observation(case):
    return {
        "observed_item_code": case["code"],
        "observed_product_name": case.get("name"),
        "observed_batch_no": case.get("batch"),
        "observed_manufacturer": case.get("manufacturer"),
        "observed_expiry_date": case.get("expiry"),
    }


def main():
    rows = []
    exact_correct = fuzzy_correct = hybrid_correct = 0
    for case in CASES:
        obs = as_observation(case)
        expected = case["expected"]
        exact_matches = [c["ItemCode"] for c in CANDIDATES if normalize_identifier(case["code"]) == normalize_identifier(c["ItemCode"])]
        exact_prediction = exact_matches[0] if len(exact_matches) == 1 else None
        fuzzy_prediction = max(CANDIDATES, key=lambda c: (_code_similarity(case["code"], c["ItemCode"]), c["ItemCode"]))["ItemCode"]
        hybrid = match_candidates(obs, CANDIDATES)
        hybrid_prediction = hybrid["top_candidate_item_code"] if hybrid["match_status"] != "NO_MATCH" else None
        exact_correct += exact_prediction == expected
        fuzzy_correct += fuzzy_prediction == expected
        hybrid_correct += hybrid_prediction == expected
        rows.append({
            "case": case["case"], "expected": expected,
            "exact_prediction": exact_prediction, "exact_correct": exact_prediction == expected,
            "fuzzy_prediction": fuzzy_prediction, "fuzzy_correct": fuzzy_prediction == expected,
            "hybrid_top_candidate": hybrid_prediction, "hybrid_top1_correct": hybrid_prediction == expected,
            "hybrid_decision": hybrid["match_status"], "hybrid_score": hybrid.get("suggested_score"),
            "hybrid_reason": hybrid.get("reason"),
        })
    n = len(CASES)
    out = {
        "dataset": "Synthetic labelled fixture corresponding to the eight manufacturer seed records",
        "cases": n,
        "metrics": {
            "exact_top1_accuracy": round(exact_correct / n, 4),
            "identifier_fuzzy_top1_accuracy": round(fuzzy_correct / n, 4),
            "hybrid_top1_candidate_accuracy": round(hybrid_correct / n, 4),
        },
        "rows": rows,
        "interpretation": "Hybrid top-1 candidate accuracy measures candidate ranking, not automatic-correction accuracy. NEEDS_REVIEW is an intentional safe outcome for ambiguous/contradictory cases.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
