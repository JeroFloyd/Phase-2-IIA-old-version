USE item_scan_db;

DROP TABLE IF EXISTS item_scan;

CREATE TABLE item_scan (
    ScanId INT PRIMARY KEY,
    ItemUniqueCode VARCHAR(20) NOT NULL,
    ScannedName VARCHAR(150) NOT NULL,
    ScanTimestamp DATETIME NOT NULL,
    ScanLocation VARCHAR(120) NOT NULL,
    UNIQUE KEY uq_scan_code (ScanId, ItemUniqueCode)
);
CREATE INDEX idx_scan_item_code ON item_scan(ItemUniqueCode);
