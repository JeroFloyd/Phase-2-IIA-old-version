-- Run the appropriate statement against each source DB to show populated tuples.

-- Manufacturer
SELECT * FROM manufacturer_db.manufactured_product;

-- Distributor
SELECT * FROM distributor_db.shipment;

-- Retailer
SELECT * FROM retailer_db.sale_record;

-- Item Scan
SELECT * FROM item_scan_db.item_scan;

-- Authority
SELECT * FROM authority_db.consumer_report;
