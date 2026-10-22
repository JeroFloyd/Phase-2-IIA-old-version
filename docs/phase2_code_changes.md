# Phase 2 implementation changes and code highlights

This log compares the Part A source archive with the current Phase 2 working copy. It documents the implementation changes in this branch; add your own brief notes if you make further local edits before the evaluation.

## New code

- `mediator/entity_matcher.py`: candidate ranking with raw and OCR-normalized identifier similarity, weighted contextual fields, structured batch matching, conflict flags, a top-two margin, and `AUTO_MATCHED` / `NEEDS_REVIEW` / `NO_MATCH` decisions.
- `mediator/ocr.py`: local image preprocessing, Tesseract OCR call, and labelled-field extraction. Raw OCR text is retained separately from parsed fields.
- `databases/item_scan/04_phase2_resolution.sql`: additive, repeatable creation of `phase2_observation_resolution`; it does not drop or alter the Part A tables.
- `tests/test_entity_matching.py`: unit tests for matching safeguards, OCR parsing, and conservative integration decisions.
- `scripts/evaluate_matching.py`: labelled synthetic comparison of exact, identifier-only fuzzy and hybrid ranking.
- `examples/sample_medicine_label_noisy_MED100Z.png` and `examples/sample_medicine_label_OCR_confusion.png`: explicitly synthetic OCR demo fixtures.

## Modified code

- `mediator/connections.py`: added parameterized `fetch_rows` and transaction-aware `execute_write` helpers in addition to the existing one-code source query.
- `mediator/main.py`: added `/phase2/algorithm-info`, `/phase2/match`, `/phase2/cleanse`, `/phase2/resolutions`, and `/phase2/reverse-match/{canonical_item_code}`. Canonical candidates are fetched from the live manufacturer view for each match request. Saved resolutions go only to the new Phase 2 table.
- `mediator/result_integrator.py`: ASALI now requires a successfully queried authority source with an explicit `NO_ADVERSE_REPORT`, plus the required manufacturer/distributor/retailer/scan evidence. A failed authority query or missing authority row returns `UNVERIFIED` instead of inferring that no adverse report exists.
- `gui/app.py`: preserves Part A verification and adds a Phase 2 image/OCR, candidate ranking, safe resolution-save, reverse-matching, and audit-results tab.
- `mediator/schema_matcher.py`: domain aliases remain explicitly accepted, but the lexical-similarity number now reflects actual string similarity instead of being forced to 1.0.
- `requirements.txt`, launch scripts, two-computer environment example and documentation were updated for local OCR and native Windows MySQL on port 3306.
- `sql/source_queries.sql` and `docs/demo_script.md`: corrected examples to reflect the actual manufacturer schema and MED1008 seed evidence.

## Key safeguards to point out in a viva

1. No mutation is performed just by uploading an image or ranking candidates.
2. A noisy record preserves its raw OCR text.
3. Candidate records are read live; there is no hardcoded eight-code candidate catalogue in the matcher.
4. A known batch conflict blocks automatic cleansing.
5. Human-approved corrections are explicitly marked in the audit table.
6. SQL values are bound as parameters. The only write SQL is the application-authored insert into the Phase 2 audit table.
7. The additive migration does not rerun or drop Part A tables.
