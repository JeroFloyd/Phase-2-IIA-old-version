USE retailer_db;
CREATE OR REPLACE VIEW retailer_item_view AS
SELECT sr.Barcode AS ItemCode,
       rs.store_name AS Retailer,
       rs.city AS RetailCity,
       sr.PurchaseDate,
       sr.SalePrice
FROM sale_record sr
JOIN retail_store rs ON rs.store_id = sr.store_id;
