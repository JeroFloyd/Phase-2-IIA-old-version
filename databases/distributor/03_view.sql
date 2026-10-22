USE distributor_db;
CREATE OR REPLACE VIEW distributor_item_view AS
SELECT s.SKU AS ItemCode,
       sp.supplier_name AS Distributor,
       s.VendorName AS Vendor,
       s.DispatchDate,
       s.Quantity
FROM shipment s
JOIN supplier sp ON sp.supplier_id = s.supplier_id;
