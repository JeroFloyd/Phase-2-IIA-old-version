# Live mutation test notes

The matcher queries `manufacturer_item_view` on every request and reverse matching reads `item_scan` on every request. Use SQL on the actual source database (not a Python fixture) to demonstrate that current records affect subsequent results.

## Before testing

- Back up the relevant source databases.
- Choose a unique temporary code and manufacturer ID; confirm they do not exist.
- Record the exact values you inserted so you can remove only your test rows.
- On the teammate's Windows server, perform mutation tests using an authorized Workbench account. The mediator's `ii_user` should remain limited to reading canonical/source data and inserting audit rows in the Phase 2 table.

## Insert a temporary canonical medicine (example IDs must be checked first)

On the Ubuntu manufacturer DB, inspect current identifiers first:

```sql
SELECT manufacturer_id, legal_name FROM manufacturer_company ORDER BY manufacturer_id;
SELECT ProductCode FROM manufactured_product WHERE ProductCode = 'MED2001';
```

If `manufacturer_id = 99` and `ProductCode = 'MED2001'` are unused, an administrator can run:

```sql
INSERT INTO manufacturer_company (manufacturer_id, legal_name, country)
VALUES (99, 'Phase Two Demo Labs', 'India');

INSERT INTO manufactured_product
(ProductCode, ProductName, manufacturer_id, BatchNo, MfgDate, ExpiryDate)
VALUES
('MED2001', 'Metformin 500 mg Tablet', 99, 'P2M26A01', '2026-05-01', '2028-04-30');
```

Now call `/phase2/match` with `MED2001` or a noisy version and matching context. Because the API reads the live view on each request, the new record should be returned without restarting the mediator. If the IDs were already used, choose different unused values first.

## Modify and delete the temporary record

```sql
UPDATE manufactured_product
SET ProductName = 'Metformin 500 mg Tablet Modified'
WHERE ProductCode = 'MED2001';
```

Run matching again and confirm candidate context reflects the changed product name.

Delete child row before parent row because of the foreign key:

```sql
DELETE FROM manufactured_product WHERE ProductCode = 'MED2001';
DELETE FROM manufacturer_company WHERE manufacturer_id = 99;
```

Replace `99`/`MED2001` with the IDs you actually used. Only delete rows that you personally inserted for this test.

## Remote scan observations

On the teammate's `item_scan_db`, insert/update/delete a clearly labelled temporary `item_scan` row using the actual column names from `databases/item_scan/01_schema.sql`. Then call `/phase2/reverse-match/<canonical-code>` again. The result should reflect the current scan rows because no candidate list is cached in the API.
