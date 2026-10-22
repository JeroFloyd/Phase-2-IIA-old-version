USE item_scan_db;
CREATE OR REPLACE VIEW scan_item_view AS
SELECT ItemUniqueCode AS ItemCode,
       ScannedName,
       ScanTimestamp,
       ScanLocation
FROM item_scan;
