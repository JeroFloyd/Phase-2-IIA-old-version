USE manufacturer_db;
CREATE OR REPLACE VIEW manufacturer_item_view AS
SELECT mp.ProductCode AS ItemCode,
       mp.ProductName,
       mc.legal_name AS Manufacturer,
       mp.BatchNo,
       mp.MfgDate AS ManufactureDate,
       mp.ExpiryDate
FROM manufactured_product mp
JOIN manufacturer_company mc ON mc.manufacturer_id = mp.manufacturer_id;
