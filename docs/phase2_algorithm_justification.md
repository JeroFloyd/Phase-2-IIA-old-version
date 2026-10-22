# Phase 2 matching algorithm and rationale

## Objective

Given text observed on a medicine-label image, retrieve plausible canonical medicine records from the live `manufacturer_item_view`, rank them, and either return a supported match or abstain. In the opposite direction, take a canonical medicine and find approximately matching observations in the live `item_scan` table and Phase 2 resolution audit table when available.

## Components

1. **Normalization.** Uppercase and remove separators for identifier comparison while retaining the original OCR text. Apply conservative `O/0` and `I/L/1` normalization only after an alphabetic prefix. This is a comparison variant, not an overwrite of the raw observed identifier.
2. **Identifier similarity.** Use RapidFuzz ratio on the raw normalized identifier and on the OCR-normalized variant; keep the higher similarity.
3. **Context scores.** Product name and manufacturer use normalized WRatio similarity. Batch is treated as a structured identifier: an exact match after the same conservative OCR-confusion variants receives 100; a different batch receives 0 and is a conflict. Expiry is compared using normalized date representations when parseable.
4. **Weighted score.** Initial configurable weights are code 0.62, product name 0.14, batch 0.16, manufacturer 0.05, expiry 0.03. Missing context is omitted and the available weights are renormalized. The same settings are exposed by `/phase2/algorithm-info`.
5. **Decision safeguards.** A raw exact canonical identifier with no contradiction can match exactly. A noisy identifier requires corroborating context, a score of at least 90, a top-two margin of at least 8, and no detected batch/expiry conflict. Strong batch/expiry/product/manufacturer contradictions or close candidates lead to `NEEDS_REVIEW`; weak candidates lead to `NO_MATCH`.
6. **Cleansing/audit.** The original OCR text and observed fields are preserved. A canonical value is stored automatically only for an `AUTO_MATCHED` result. A listed candidate can instead be saved as `MANUALLY_APPROVED` when a human explicitly reviews and approves it. Review/no-match records do not get a canonical code by default.

## Why hybrid rather than edit distance alone?

Medicine codes may share most characters, and distinct products can have very similar codes. In this seed data, `MED1001` and `MED1002` share the same product name and manufacturer but different batch numbers. Identifier-only matching is therefore insufficient for a conflicting/ambiguous case. Batch agreement can help distinguish those records; a batch contradiction blocks automatic correction.

## Limits

These initial weights and thresholds are transparent engineering settings, not a claim of globally optimal accuracy. Use `scripts/evaluate_matching.py` and expand its labelled test cases before describing accuracy. Results currently reflect a small, synthetic, eight-record catalogue and six labelled test cases only. OCR can still fail on blur, glare, rotation, small characters, or layouts outside the label parser's patterns; the UI therefore exposes raw text and editable extracted fields.
