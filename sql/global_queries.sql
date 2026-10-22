-- Global/mediated query exposed by the mediator.
-- There is intentionally NO physical ItemHistory table in a central database.
-- The mediator accepts this query, decomposes it, queries the five source views,
-- and integrates the returned tuples.

SELECT *
FROM ItemHistory
WHERE ItemCode = 'MED1001';

SELECT *
FROM ItemHistory
WHERE ItemCode = 'MED1002';

SELECT *
FROM ItemHistory
WHERE ItemCode = 'MED1003';

SELECT *
FROM ItemHistory
WHERE ItemCode = 'MED1008';

SELECT *
FROM ItemHistory
WHERE ItemCode = 'MED9999';
