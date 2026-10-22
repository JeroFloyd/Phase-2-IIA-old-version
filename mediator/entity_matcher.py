"""Entity matching for noisy medicine identifiers.

This module is deliberately database-independent. The API layer passes in the
current canonical candidates retrieved from MySQL, so no catalogue is cached or
hardcoded here.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

from rapidfuzz import fuzz

# Weights sum to 1.0. They are initial, interpretable settings to evaluate on the
# included labelled synthetic cases; they are not claimed to be universally optimal.
WEIGHTS = {
    "code": 0.62,
    "product_name": 0.14,
    "batch_no": 0.16,
    "manufacturer": 0.05,
    "expiry_date": 0.03,
}
AUTO_MATCH_SCORE = 90.0
AUTO_MATCH_MARGIN = 8.0
NO_MATCH_SCORE = 65.0
MAX_RETURN_CANDIDATES = 10


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value).strip()


def normalize_identifier(value: Any) -> str:
    """Remove separators and normalize case without changing characters."""
    return re.sub(r"[^A-Z0-9]", "", _text(value).upper())


def ocr_normalize_identifier(value: Any) -> str:
    """Apply conservative O/0 and I/1 corrections only after an alpha prefix.

    Example: MED1OO2 -> MED1002. We intentionally do not globally replace O
    with 0 because letters can be valid in identifiers outside the numeric part.
    """
    cleaned = normalize_identifier(value)
    match = re.fullmatch(r"([A-Z]+)([A-Z0-9]+)", cleaned)
    if not match:
        return cleaned
    prefix, suffix = match.groups()
    # Only the suffix is treated as potentially numeric. Keep other characters
    # unchanged so that the fuzzy matcher can still evaluate them as noise.
    suffix = suffix.replace("O", "0").replace("I", "1").replace("L", "1")
    return prefix + suffix


def _normal_text(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", _text(value).upper())


def _normal_date(value: Any) -> str:
    raw = _text(value)
    if not raw:
        return ""
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return _normal_text(raw)


def _similarity(left: Any, right: Any) -> float | None:
    a, b = _normal_text(left), _normal_text(right)
    if not a or not b:
        return None
    return float(fuzz.WRatio(a, b))


def _code_similarity(observed: Any, canonical: Any) -> float:
    raw = normalize_identifier(observed)
    corrected = ocr_normalize_identifier(observed)
    target = normalize_identifier(canonical)
    if not raw or not target:
        return 0.0
    return float(max(fuzz.ratio(raw, target), fuzz.ratio(corrected, target)))


def _candidate_value(candidate: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in candidate and candidate[name] is not None:
            return candidate[name]
    return None


def score_candidate(observation: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Score one observation/canonical-record pair and retain explanations."""
    observed_code = observation.get("observed_item_code") or observation.get("item_code") or ""
    canonical_code = _candidate_value(candidate, "ItemCode", "item_code", "ProductCode") or ""
    code_score = _code_similarity(observed_code, canonical_code)

    observed_name = observation.get("observed_product_name") or observation.get("product_name")
    observed_batch = observation.get("observed_batch_no") or observation.get("batch_no")
    observed_manufacturer = observation.get("observed_manufacturer") or observation.get("manufacturer")
    observed_expiry = observation.get("observed_expiry_date") or observation.get("expiry_date")

    candidate_name = _candidate_value(candidate, "ProductName", "product_name")
    candidate_batch = _candidate_value(candidate, "BatchNo", "batch_no")
    candidate_manufacturer = _candidate_value(candidate, "Manufacturer", "manufacturer")
    candidate_expiry = _candidate_value(candidate, "ExpiryDate", "expiry_date")

    name_score = _similarity(observed_name, candidate_name)
    manufacturer_score = _similarity(observed_manufacturer, candidate_manufacturer)

    batch_score: float | None = None
    batch_conflict = False
    batch_ocr_helped = False
    if _text(observed_batch) and _text(candidate_batch):
        observed_batch_normal = normalize_identifier(observed_batch)
        candidate_batch_normal = normalize_identifier(candidate_batch)
        observed_batch_ocr = ocr_normalize_identifier(observed_batch)
        candidate_batch_ocr = ocr_normalize_identifier(candidate_batch)
        batch_variants = {
            observed_batch_normal,
            observed_batch_ocr,
        }
        candidate_batch_variants = {
            candidate_batch_normal,
            candidate_batch_ocr,
        }
        # Batch identifiers are structured identifiers: do not reward a nearly
        # matching but different batch. Only exact equality after conservative
        # OCR-confusion normalization counts as a match.
        batch_score = 100.0 if batch_variants.intersection(candidate_batch_variants) else 0.0
        batch_ocr_helped = batch_score == 100.0 and observed_batch_normal != candidate_batch_normal
        batch_conflict = batch_score < 100.0

    expiry_score: float | None = None
    expiry_conflict = False
    if _text(observed_expiry) and _text(candidate_expiry):
        left, right = _normal_date(observed_expiry), _normal_date(candidate_expiry)
        expiry_score = 100.0 if left == right else float(fuzz.ratio(left, right))
        # A fully parseable but conflicting expiry date is a warning that blocks
        # automatic correction; OCR may have misread the date and needs review.
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", left) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", right):
            expiry_conflict = left != right

    components: dict[str, float | None] = {
        "code_similarity": round(code_score, 2),
        "product_name_similarity": round(name_score, 2) if name_score is not None else None,
        "batch_match": round(batch_score, 2) if batch_score is not None else None,
        "manufacturer_similarity": round(manufacturer_score, 2) if manufacturer_score is not None else None,
        "expiry_match": round(expiry_score, 2) if expiry_score is not None else None,
    }

    weighted_sum = WEIGHTS["code"] * code_score
    weight_total = WEIGHTS["code"]
    available_context = 0
    for key, value in (
        ("product_name", name_score),
        ("batch_no", batch_score),
        ("manufacturer", manufacturer_score),
        ("expiry_date", expiry_score),
    ):
        if value is not None:
            weighted_sum += WEIGHTS[key] * value
            weight_total += WEIGHTS[key]
            available_context += 1
    final_score = weighted_sum / weight_total if weight_total else 0.0

    raw_exact = normalize_identifier(observed_code) == normalize_identifier(canonical_code)
    ocr_corrected = ocr_normalize_identifier(observed_code) == normalize_identifier(canonical_code) and not raw_exact
    conflicts = []
    if batch_conflict:
        conflicts.append("observed batch number conflicts with candidate batch")
    if expiry_conflict:
        conflicts.append("observed expiry date conflicts with candidate expiry")
    if name_score is not None and name_score < 70:
        conflicts.append("observed product name strongly conflicts with candidate product name")
    if manufacturer_score is not None and manufacturer_score < 60:
        conflicts.append("observed manufacturer strongly conflicts with candidate manufacturer")

    corroboration = (
        (batch_score == 100.0)
        or (name_score is not None and name_score >= 90 and (
            (manufacturer_score is not None and manufacturer_score >= 90)
            or expiry_score == 100.0
        ))
    )
    return {
        "item_code": _text(canonical_code),
        "product_name": _text(candidate_name),
        "manufacturer": _text(candidate_manufacturer),
        "batch_no": _text(candidate_batch),
        "expiry_date": _text(candidate_expiry),
        **components,
        "final_score": round(final_score, 2),
        "raw_identifier_exact": raw_exact,
        "ocr_normalization_helped": ocr_corrected,
        "batch_ocr_normalization_helped": batch_ocr_helped,
        "context_fields_compared": available_context,
        "context_conflicts": conflicts,
        "has_context_corroboration": bool(corroboration),
    }


def match_candidates(observation: dict[str, Any], candidates: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Rank current canonical candidates and return a cautious resolution state."""
    all_ranked = [score_candidate(observation, row) for row in candidates]
    all_ranked.sort(key=lambda x: (x["final_score"], x["code_similarity"], x["batch_match"] or 0), reverse=True)

    observed = _text(observation.get("observed_item_code") or observation.get("item_code"))
    if not observed:
        return {
            "match_status": "NO_MATCH", "suggested_item_code": None,
            "suggested_score": 0.0, "margin": 0.0,
            "reason": "No usable item code was extracted or entered.", "candidates": [],
        }
    if not all_ranked:
        return {
            "match_status": "NO_MATCH", "suggested_item_code": None,
            "suggested_score": 0.0, "margin": 0.0,
            "reason": "The live manufacturer catalogue returned no candidate records.", "candidates": [],
        }

    best = all_ranked[0]
    second_score = all_ranked[1]["final_score"] if len(all_ranked) > 1 else 0.0
    margin = round(best["final_score"] - second_score, 2)
    raw_exact = best["raw_identifier_exact"]
    conflicts = best["context_conflicts"]
    # If the observed code exactly names one catalogue record but context ranks
    # a different medicine first, preserve the ambiguity for human review. Search
    # the full ranked list for the exact code even if it falls outside top 10.
    exact_code_record = next((row for row in all_ranked if row["raw_identifier_exact"]), None)
    exact_code_context_disagreement = bool(
        exact_code_record and exact_code_record["item_code"] != best["item_code"]
    )
    # Exact canonical code can be accepted without context only if the supplied
    # context does not contradict it. OCR-corrected values need context evidence.
    exact_unconflicted = raw_exact and not conflicts
    auto_supported = (
        exact_unconflicted
        or (
            best["final_score"] >= AUTO_MATCH_SCORE
            and margin >= AUTO_MATCH_MARGIN
            and best["has_context_corroboration"]
            and not conflicts
            and not exact_code_context_disagreement
        )
    )

    if exact_code_context_disagreement:
        status = "NEEDS_REVIEW"
        reason = (
            f"The observed code exactly matches {exact_code_record['item_code']}, but contextual evidence ranks "
            f"{best['item_code']} higher. Do not silently replace an exact code; human review is required."
        )
    elif auto_supported:
        status = "AUTO_MATCHED"
        reason = "The top candidate meets the current score/margin rule and has no detected contextual contradiction."
        if raw_exact:
            reason = "The observed identifier exactly matches a canonical code and the available context does not contradict it."
        elif best["ocr_normalization_helped"]:
            reason = "OCR-aware normalization aligns the identifier; contextual evidence corroborates the candidate and no hard conflict was found."
    elif best["final_score"] < NO_MATCH_SCORE:
        status = "NO_MATCH"
        reason = "No candidate reached the minimum review score; no canonical code was assigned."
    else:
        status = "NEEDS_REVIEW"
        if conflicts:
            reason = "The leading candidate has contextual contradictions: " + "; ".join(conflicts) + ". Human review is required."
        elif margin < AUTO_MATCH_MARGIN:
            reason = "The leading candidates are too close to auto-resolve safely. Human review is required."
        elif not best["has_context_corroboration"] and not raw_exact:
            reason = "The noisy identifier lacks sufficient corroborating context for automatic cleansing."
        else:
            reason = "The candidate is plausible but does not satisfy all auto-match safeguards. Human review is required."

    return {
        "observed_item_code": observed,
        "match_status": status,
        "suggested_item_code": best["item_code"] if status == "AUTO_MATCHED" else None,
        "top_candidate_item_code": best["item_code"],
        "suggested_score": best["final_score"],
        "margin": margin,
        "reason": reason,
        "scoring": {
            "weights": WEIGHTS,
            "automatic_match_threshold": AUTO_MATCH_SCORE,
            "minimum_margin": AUTO_MATCH_MARGIN,
            "hard_context_conflicts_block_auto_match": True,
        },
        "candidates": all_ranked[:MAX_RETURN_CANDIDATES],
    }


def score_observation_against_canonical(scan_row: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    """Score a noisy scan observation against one selected canonical record."""
    observation = {
        "observed_item_code": scan_row.get("ObservedItemCode") or scan_row.get("ItemUniqueCode") or scan_row.get("observed_item_code"),
        "observed_product_name": scan_row.get("ObservedProductName") or scan_row.get("ScannedName") or scan_row.get("observed_product_name"),
        "observed_batch_no": scan_row.get("ObservedBatchNo") or scan_row.get("observed_batch_no"),
        "observed_manufacturer": scan_row.get("ObservedManufacturer") or scan_row.get("observed_manufacturer"),
        "observed_expiry_date": scan_row.get("ObservedExpiryDate") or scan_row.get("observed_expiry_date"),
    }
    return score_candidate(observation, canonical)
