# Part A Rubric Mapping

| Rubric item | Evidence in this project |
|---|---|
| 1. Define scope | `docs/project_scope.md` + GUI description |
| 2. New / innovative aspects | Distributed, source-autonomous medicine history verification using heterogeneous schemas and a mediated global query |
| 3. Database schema design (2) | Five independent MySQL schemas under `databases/` |
| 4. Populate data (2) | Five `02_seed.sql` files with controlled synthetic records and cross-source identifiers |
| 5. Schema matching / mapping (2) | `mediator/schema_matcher.py`, source views, fixed parameterized queries, and `docs/schema_mapping.md`; `mediator/mappings.py` is reference metadata, not dynamically executed by the planner |
| 6. Seamless SQL decomposition and federation (2) | `mediator/query_decomposer.py`, `/query`, `/plan`, and source-specific SQL execution |
| 7. Establish communication between data sources (2) | Five separate MySQL connections through `mysql-connector-python`; configurable host/port for a second machine |
| 8. Query result integration + GUI (3) | `mediator/result_integrator.py` and `gui/app.py`; GUI displays integrated table and federation trace |
