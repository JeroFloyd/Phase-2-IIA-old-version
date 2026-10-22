USE retailer_db;

INSERT INTO retail_store VALUES
(101, 'HealthMart', 'Delhi'),
(102, 'CityCare Pharmacy', 'Delhi'),
(103, 'WellLife Pharmacy', 'Gurugram');

INSERT INTO sale_record VALUES
(7001, 'MED1001', 101, '2026-02-02', 34.00),
(7002, 'MED1002', 101, '2026-02-03', 31.00),
(7003, 'MED1003', 102, '2026-03-05', 119.00),
(7004, 'MED1004', 103, '2026-03-12', 88.00),
(7005, 'MED1005', 102, '2026-03-25', 55.00),
(7006, 'MED1006', 101, '2026-04-04', 92.00),
(7007, 'MED1007', 103, '2026-04-10', 41.00),
(7008, 'MED9999', 101, '2026-04-12', 25.00);
-- MED9999 exists only in downstream retail/scan evidence, not the manufacturer source.
