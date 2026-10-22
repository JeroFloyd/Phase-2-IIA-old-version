# Phase 2 test results

## Environment and command

Run from the project root with dependencies installed:

```bash
python -m unittest discover -s tests -v
python scripts/evaluate_matching.py
```

## Current local verification

- Python syntax compilation: all Python source files compiled successfully during packaging checks.
- Unit tests: **12 passed** in the current implementation.
- OCR smoke check: Tesseract extracted the labelled fields from both included synthetic label PNGs in the implementation environment. The intentionally noisy `MED100Z` image produced parsed fields `MED100Z`, `ORS Powder Sachet`, batch text `CN24012`, manufacturer `CureNova Pharmaceuticals`, and expiry `2028-03-18`; the batch OCR confusion is matched against canonical batch `CN24O12` using a comparison-only O/0 variant.
- Six-case labelled synthetic evaluation: exact top-1 accuracy **0.50**, identifier-fuzzy-only top-1 accuracy **0.50**, hybrid top-1 candidate accuracy **1.00**.

## Interpreting the result honestly

The six cases are intentionally selected test fixtures based on the eight seeded canonical medicine records. Top-1 candidate accuracy measures whether the correct candidate is ranked first; it does **not** mean all six cases were automatically cleansed. One conflicting-code/batch case is correctly labelled `NEEDS_REVIEW`, and the unknown item is `NO_MATCH`. The numeric result is a development smoke evaluation, not a statistically representative estimate of real-world OCR/entity-matching accuracy.

The unit tests cover OCR text parsing, code-confusion normalization, contextual disambiguation, batch-conflict safeguards, reverse-direction scoring, abstention without context, unknown identifiers, and conservative Part A decision behavior when authority evidence is absent or the authority query fails.

## Live database checks still required on the student's two laptops

- Run `/health` and check all five Part A sources.
- Run `/phase2/match` on `MED100Z` with ORS/batch/manufacturer/expiry context and verify `MED1007` is the top candidate.
- Run `/phase2/cleanse` after applying the additive migration and permission grant, then read `/phase2/resolutions`.
- Run `/phase2/reverse-match/MED1002` and check both existing scans and saved Phase 2 observations where the audit table is available.
- Insert, update and delete a **clearly identified test record** on the source catalogue/scan table and confirm the next request reads the current database contents without restarting the mediator.
- Re-run the original `MED1001`, `MED1002` and `MED1008` Part A tests after all changes.
