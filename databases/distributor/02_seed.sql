USE distributor_db;

INSERT INTO supplier VALUES
(11, 'MedSupply Distributors', 'MSD-IND-4401'),
(12, 'PrimeCare Wholesale', 'PCW-IND-5512'),
(13, 'SafeMeds Distribution Co', 'SMD-IND-6631');

INSERT INTO shipment VALUES
(5001, 11, 'MED1001', 'HealthMart - Delhi', '2026-01-20', 500),
(5002, 11, 'MED1002', 'HealthMart - Delhi', '2026-01-21', 500),
(5003, 12, 'MED1003', 'CityCare Pharmacy', '2026-02-20', 300),
(5004, 13, 'MED1004', 'WellLife Pharmacy', '2026-03-01', 250),
(5005, 12, 'MED1005', 'CityCare Pharmacy', '2026-03-10', 400),
(5006, 11, 'MED1006', 'HealthMart - Delhi', '2026-03-20', 450),
(5007, 13, 'MED1007', 'WellLife Pharmacy', '2026-03-28', 350);
-- MED1008 intentionally has no distributor shipment to demonstrate incomplete provenance.
