# Asali Nakali — Part A + Phase 2

An information-integration prototype for medicine history verification across **five independent MySQL data sources**, extended with noisy medicine-label OCR, bidirectional entity matching and auditable record cleansing.

## Architecture

**Mediation / federated virtual integration**

```text
3 source databases on Computer A + 2 source databases on Computer B
                              |
                              v
                      source-specific views
                              |
                              v
                  mediator / global ItemHistory
                  |  query decomposition
                  |  source query execution
                  |  result integration
                  |  schema mapping evidence
                              |
                              v
                        Streamlit GUI

Phase 2 addition:
medicine-label image -> local OCR -> candidate ranking/context
-> AUTO_MATCHED / NEEDS_REVIEW / NO_MATCH -> resolution audit table
-> existing federated lookup after canonical resolution
```

## Dependencies

- Docker Engine + Compose for the local source containers, or the existing native MySQL setup.
- Python 3.12+ for the mediator/GUI virtual environment.
- Tesseract executable for OCR. On Ubuntu:

```bash
sudo apt update
sudo apt install -y tesseract-ocr python3-full python3-venv
```

## Fast start: one-computer local Docker setup

This configuration runs all five source databases locally and is useful for development/regression tests. It is not the required 3+2 physical split demo.

```bash
docker compose up -d --build
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

In Terminal 1:

```bash
source .venv/bin/activate
./run_mediator.sh
```

In Terminal 2:

```bash
source .venv/bin/activate
./run_gui.sh
```

Open `http://localhost:8501`. Check `http://127.0.0.1:8000/health` first.

## Two-computer demo setup (the presentation topology)

- Computer A / Ubuntu: Manufacturer DB `127.0.0.1:3307`, Distributor DB `127.0.0.1:3308`, Retailer DB `127.0.0.1:3309`, mediator port 8000, GUI port 8501.
- Computer B / teammate Windows laptop: native MySQL Server on port 3306 holding `item_scan_db` and `authority_db`.

Copy `.env.two-computer.example` to `.env` on Computer A and replace `TEAMMATE_LAN_IP` with Computer B's current LAN IPv4 address. The two remote sources both use port 3306. See `docs/two_computer_demo.md`.

For Phase 2 persistent resolution records, on Computer B run `databases/item_scan/04_phase2_resolution.sql` as an administrator, then grant `SELECT, INSERT` on only `item_scan_db.phase2_observation_resolution` to the existing integration account. See `docs/phase2_database_setup.md`. This is required for saving/listing cleansing records but not for the read-only `/phase2/match` candidate search.

## Part A endpoints

- `GET /health` — checks the five source connections.
- `GET /plan?item_code=MED1001` — shows the five source subqueries.
- `GET /schema-matches` — shows schema-attribute matches.
- `GET /verify/MED1001` — performs federation.
- `POST /query` — executes the supported global SQL form.

## Phase 2 endpoints

- `GET /phase2/algorithm-info` — exposes the matching weights/thresholds and rationale.
- `POST /phase2/match` — ranks canonical candidates from the live manufacturer view; does not write data.
- `POST /phase2/cleanse` — recomputes the decision and inserts an auditable resolution record into the Phase 2 table.
- `GET /phase2/resolutions?limit=20` — reads saved resolution records.
- `GET /phase2/reverse-match/MED1002` — returns approximate matching observations from the live scan table and, when installed/accessible, the Phase 2 resolution table.

Example match request:

```bash
curl -s -X POST http://127.0.0.1:8000/phase2/match \
  -H 'Content-Type: application/json' \
  -d '{"raw_ocr_text":"ITEM CODE: MED1OO2","observed_item_code":"MED1OO2","observed_product_name":"Paracetamol 500 mg Tablet","observed_batch_no":"AX24P02","observed_manufacturer":"Apex Lifesciences Pvt Ltd","observed_expiry_date":"2028-01-11"}' | python3 -m json.tool
```

## Synthetic labels and tests

- `examples/sample_medicine_label_noisy_MED100Z.png` — noisy code with contextual fields supporting MED1007.
- `examples/sample_medicine_label_OCR_confusion.png` — label with visually confusable O/0 characters; OCR may itself resolve the glyphs correctly.

Run automated tests and the labelled matching comparison:

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
python scripts/evaluate_matching.py
```

The small evaluation fixture is synthetic and intentionally limited. It is useful as a reproducible development comparison, not a claim of universal real-world accuracy. See `docs/phase2_test_results.md` and `docs/phase2_algorithm_justification.md`.

## Important data-safety notes

- Do not casually rerun `databases/*/01_schema.sql` on populated live databases: those Part A scripts can drop tables.
- `databases/item_scan/04_phase2_resolution.sql` is an additive migration and does not drop/alter the Part A tables.
- OCR text is retained as raw observation; the matching layer does not silently overwrite it.
- Only automatic matches that pass the score, margin and context checks receive a canonical code automatically. Contradictory or ambiguous cases require review.
- Do not include the real `.env` in the submission archive.
