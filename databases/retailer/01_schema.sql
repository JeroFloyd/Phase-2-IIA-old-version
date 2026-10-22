USE retailer_db;

DROP TABLE IF EXISTS sale_record;
DROP TABLE IF EXISTS retail_store;

CREATE TABLE retail_store (
    store_id INT PRIMARY KEY,
    store_name VARCHAR(120) NOT NULL,
    city VARCHAR(80) NOT NULL
);

CREATE TABLE sale_record (
    SaleId INT PRIMARY KEY,
    Barcode VARCHAR(20) NOT NULL,
    store_id INT NOT NULL,
    PurchaseDate DATE NOT NULL,
    SalePrice DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (store_id) REFERENCES retail_store(store_id)
);
CREATE INDEX idx_sale_barcode ON sale_record(Barcode);
