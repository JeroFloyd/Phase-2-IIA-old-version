# Phase 2 demo plan

## Pre-demo setup

1. Start the three local database containers on the mediator/Ubuntu laptop.
2. Ensure the teammate's Windows MySQL Server is running and reachable at its current LAN IP on TCP 3306.
3. Copy `.env.two-computer.example` to `.env`, set the current teammate IP for both `SCAN_HOST` and `AUTH_HOST`, and confirm ports 3306.
4. In the teammate's Workbench, run `databases/item_scan/04_phase2_resolution.sql` as an administrator and grant `SELECT, INSERT` on only `item_scan_db.phase2_observation_resolution` to the integration user as described in `phase2_database_setup.md`.
5. Activate the venv, install `requirements.txt`, install the system Tesseract executable (`sudo apt install tesseract-ocr` on Ubuntu), start `./run_mediator.sh`, then start `./run_gui.sh` in another terminal.
6. Verify `curl -s http://127.0.0.1:8000/health` reports all five source statuses as `success`.

## Primary image demo

1. In the Phase 2 tab, upload `examples/sample_medicine_label_noisy_MED100Z.png`. This is explicitly synthetic test data, not a real medicine label.
2. Click **EXTRACT TEXT WITH OCR**. Expected extracted context: noisy code `MED100Z`, product `ORS Powder Sachet`, batch read possibly as `CN24012`, manufacturer `CureNova Pharmaceuticals`, expiry `2028-03-18`.
3. Click **FIND APPROXIMATE MATCHES**. Expected top candidate is canonical `MED1007` because the product/manufacturer/expiry and OCR-aware batch comparison support it. The score is computed at runtime from the live manufacturer view.
4. Save the algorithm decision. With the current labelled seed catalogue the result should be `AUTO_MATCHED` and `MED1007`. If the underlying data has changed, explain and inspect the actual result rather than claiming the seed result must remain unchanged.
5. Show the audit record through **LOAD RECENT CLEANSING AUDIT RECORDS**.
6. In reverse matching, enter `MED1007` and show the approximate existing scan observations and any saved Phase 2 observations.
7. Open `phase2_algorithm_justification.md` and explain code similarity, contextual evidence, batch conflict safeguards, and why ambiguous results are sent to review.

## Demonstrate safe ambiguity handling

Enter observed code `MED1001` but batch `AX24P02`, with Paracetamol/manufacturer/expiry context matching MED1002. Expected top candidate is `MED1002`, but the status should be `NEEDS_REVIEW`; the exact-code candidate's batch/expiry conflict prevents an automatic correction. This is a deliberately designed ambiguity/conflict example.

## Live insert/update/delete check

Use a dedicated, identified test record in MySQL. After insert/update/delete, click **FIND APPROXIMATE MATCHES** again. Matching reads the live catalogue; it does not require restarting the mediator. Remove only your own test records afterwards. Do not execute the original `01_schema.sql` files against the populated databases because they contain `DROP TABLE` statements.

## Part A regression demo

Finish with the Part A tab: `MED1001` should normally produce ASALI with all expected records, `MED1002` NAKALI due to the confirmed authority report, and `MED1008` UNVERIFIED due to missing source evidence / review status. If the TA has modified these records, explain the live resulting data rather than assuming the original seed values remain.
