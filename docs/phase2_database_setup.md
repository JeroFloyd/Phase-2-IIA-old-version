# Phase 2 database setup (Windows teammate source)

This is an additive migration. It does not drop or alter `item_scan`, `scan_item_view`, or the existing Part A data.

## 1. Back up first

In MySQL Workbench, export the `item_scan_db` schema/data before applying the migration. Do not rerun `01_schema.sql` or seed scripts on a populated live database; the schema script drops the Part A table.

## 2. Create the Phase 2 audit table

On the teammate's Windows MySQL Server, open Workbench as an administrative account and run the complete file:

`databases/item_scan/04_phase2_resolution.sql`

Verify it exists:

```sql
USE item_scan_db;
SHOW TABLES LIKE 'phase2_observation_resolution';
```

## 3. Grant only the privileges needed by the mediator

Run as an administrator. This grants read access to the Phase 2 audit table and permission to create/update review records only in that table; it does not grant writes to the source `item_scan` or `consumer_report` tables.

```sql
GRANT SELECT, INSERT ON item_scan_db.phase2_observation_resolution TO 'ii_user'@'%';
FLUSH PRIVILEGES;
SHOW GRANTS FOR 'ii_user'@'%';
```

If the account is defined with a different host component, inspect `SELECT user, host FROM mysql.user WHERE user='ii_user';` and apply the grant to the exact existing account rather than creating a duplicate account unnecessarily.

## 4. Check connectivity from the mediator laptop

```bash
mysql -h TEAMMATE_LAN_IP -P 3306 -u ii_user -p -e "SELECT COUNT(*) FROM item_scan_db.item_scan; SELECT COUNT(*) FROM item_scan_db.phase2_observation_resolution;"
```

The first count is the original scan table; the second should be zero before the first Phase 2 save. `GET /phase2/match` can work before this migration because matching reads the existing manufacturer catalogue; saving audit records and reading saved resolutions require the migration and grants.
