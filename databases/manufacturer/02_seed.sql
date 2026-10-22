USE manufacturer_db;

INSERT INTO manufacturer_company VALUES
(1, 'Apex Lifesciences Pvt Ltd', 'India'),
(2, 'Bharat Health Labs', 'India'),
(3, 'CureNova Pharmaceuticals', 'India');

INSERT INTO manufactured_product VALUES
('MED1001', 'Paracetamol 500 mg Tablet', 1, 'AX24P01', '2026-01-10', '2028-01-09'),
('MED1002', 'Paracetamol 500 mg Tablet', 1, 'AX24P02', '2026-01-12', '2028-01-11'),
('MED1003', 'Azithromycin 250 mg Tablet', 2, 'BH24A11', '2026-02-05', '2028-02-04'),
('MED1004', 'Pantoprazole 40 mg Tablet', 3, 'CN24T09', '2026-02-18', '2028-02-17'),
('MED1005', 'Cetirizine 10 mg Tablet', 2, 'BH24C22', '2026-03-02', '2028-03-01'),
('MED1006', 'Amoxicillin 500 mg Capsule', 1, 'AX24M18', '2026-03-11', '2028-03-10'),
('MED1007', 'ORS Powder Sachet', 3, 'CN24O12', '2026-03-19', '2028-03-18'),
('MED1008', 'Ibuprofen 400 mg Tablet', 1, 'AX24I07', '2026-04-01', '2028-03-31');
