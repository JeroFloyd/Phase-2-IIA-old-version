# Two-computer demonstration — 3 local sources + 2 remote sources

## Required topology

**Computer A — Ubuntu / mediator laptop**
- Manufacturer DB: host port 3307
- Distributor DB: host port 3308
- Retailer DB: host port 3309
- Mediator API: port 8000
- Streamlit GUI: port 8501

**Computer B — teammate's Windows laptop**
- Native MySQL Server: port 3306
- `item_scan_db`
- `authority_db`

The two remote schemas share one MySQL server instance on Computer B but remain separate databases. The three local databases run independently in Docker on Computer A. For the actual two-computer presentation, do not run all five sources on one machine.

## 1. Computer B: Windows native MySQL

- Start the MySQL Server service and ensure Workbench connects to `127.0.0.1:3306`.
- Verify the `item_scan_db` and `authority_db` tables/views and seed records exist.
- Run the Phase 2 migration and grant described in `phase2_database_setup.md` if you need to save cleansing results.
- Find the current Windows IPv4 address with `ipconfig`.
- Permit inbound TCP 3306 from Computer A's current LAN IP only. Do not expose MySQL to the public internet.

## 2. Computer A: local source containers

```bash
docker start asali-manufacturer-db asali-distributor-db asali-retailer-db
docker ps --filter 'name=asali-' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Find the current Ubuntu Wi-Fi/LAN address:

```bash
ip addr show | grep 'inet 192.168'
```

Copy `.env.two-computer.example` to `.env`, replace `TEAMMATE_LAN_IP`, and preserve `SCAN_PORT=3306` and `AUTH_PORT=3306`.

Install dependencies and system OCR:

```bash
sudo apt install -y tesseract-ocr python3-full python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 3. Start services

Terminal 1 on Computer A:

```bash
source .venv/bin/activate
./run_mediator.sh
```

Terminal 2 on Computer A:

```bash
source .venv/bin/activate
./run_gui.sh
```

Open `http://localhost:8501`.

## 4. Verify the cross-machine connection

On Computer A:

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
mysql -h TEAMMATE_LAN_IP -P 3306 -u ii_user -p -e 'SELECT COUNT(*) FROM item_scan_db.item_scan; SELECT COUNT(*) FROM authority_db.consumer_report;'
```

Expect the first three sources to show host `127.0.0.1` on 3307–3309 and the last two to show Computer B's IP on 3306.

## 5. Demo order

1. Show Part A `MED1001`, `MED1002`, and `MED1008` if the TA asks for the original integration.
2. Open Phase 2 and upload `examples/sample_medicine_label_noisy_MED100Z.png`.
3. Run OCR, review text/context, find candidate matches, and explain the ranked scores.
4. Save the resolution after migration/permissions are installed; show the audit row.
5. Run reverse matching for `MED1007` to show approximately matching existing observations.
6. Show `docs/phase2_algorithm_justification.md` and `docs/phase2_test_results.md` for algorithm choice and evidence.

If the remote IP changes, update both `SCAN_HOST` and `AUTH_HOST` in `.env` and restart the mediator so the new values load.
