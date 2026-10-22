# Start Here — Phase 2

This is the Phase 2 development copy. It preserves Part A and adds OCR-aware entity matching plus an audit-table migration.

## Before running

1. Install Tesseract and Python prerequisites on the Ubuntu machine:

   ```bash
   sudo apt update
   sudo apt install -y tesseract-ocr python3-full python3-venv
   ```

2. Configure the two-computer connection:

   ```bash
   cp .env.two-computer.example .env
   ```

   Edit `.env` and replace `TEAMMATE_LAN_IP` in `SCAN_HOST` and `AUTH_HOST` with the teammate's **current** Windows IPv4. Both remote ports must be `3306`. Never submit this real `.env` file.

3. On the teammate's Windows MySQL server, as an administrator, run `databases/item_scan/04_phase2_resolution.sql`. Then run the narrow `SELECT, INSERT` grant in `docs/phase2_database_setup.md`. This is necessary to save/list cleansing audit rows. Matching itself is read-only and can be tested before the migration.

4. Start the 3 local databases. If the existing named containers are still present:

   ```bash
   docker start asali-manufacturer-db asali-distributor-db asali-retailer-db
   ```

   If those containers do not exist on the machine, use the three-source compose setup documented in `docs/two_computer_demo.md` and check ports/volumes before starting a second stack.

5. Create a Python venv and install packages:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

## Start services

Terminal 1 (keep open):

```bash
source .venv/bin/activate
./run_mediator.sh
```

Terminal 2:

```bash
source .venv/bin/activate
./run_gui.sh
```

Open `http://localhost:8501`.

## Quick verification

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
python -m unittest discover -s tests -v
python scripts/evaluate_matching.py
```

For the Phase 2 demo, upload `examples/sample_medicine_label_noisy_MED100Z.png`. OCR should extract code `MED100Z` and context. The matcher should rank `MED1007` first in the original synthetic seed data. Save the audit record only after the teammate-side migration and grant are applied.

See `docs/phase2_demo_script.md` for the complete evaluation sequence and `docs/phase2_live_mutations.md` for safe, reversible insert/update/delete demonstrations.
