USE manufacturer_db;

DROP TABLE IF EXISTS manufactured_product;
DROP TABLE IF EXISTS manufacturer_company;

CREATE TABLE manufacturer_company (
    manufacturer_id INT PRIMARY KEY,
    legal_name VARCHAR(120) NOT NULL,
    country VARCHAR(80) NOT NULL
);

CREATE TABLE manufactured_product (
    ProductCode VARCHAR(20) PRIMARY KEY,
    ProductName VARCHAR(150) NOT NULL,
    manufacturer_id INT NOT NULL,
    BatchNo VARCHAR(30) NOT NULL,
    MfgDate DATE NOT NULL,
    ExpiryDate DATE NOT NULL,
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturer_company(manufacturer_id)
);
