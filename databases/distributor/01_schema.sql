USE distributor_db;

DROP TABLE IF EXISTS shipment;
DROP TABLE IF EXISTS supplier;

CREATE TABLE supplier (
    supplier_id INT PRIMARY KEY,
    supplier_name VARCHAR(120) NOT NULL,
    license_no VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE shipment (
    shipment_id INT PRIMARY KEY,
    supplier_id INT NOT NULL,
    SKU VARCHAR(20) NOT NULL,
    VendorName VARCHAR(120) NOT NULL,
    DispatchDate DATE NOT NULL,
    Quantity INT NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
);
CREATE INDEX idx_shipment_sku ON shipment(SKU);
