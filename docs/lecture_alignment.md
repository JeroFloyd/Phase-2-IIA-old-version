# Lecture Alignment

## Week 2: Information integration architectures

The project uses mediation/federated virtual integration. Data remains in separate MySQL sources and the mediator queries sources at request time instead of creating a centralized warehouse copy.

## Week 3: Schema matching and mappings

The project demonstrates attribute correspondences across heterogeneous source names. In the current runtime, predefined source views and parameterized queries execute the mappings. `mediator/mappings.py` documents correspondences but is not dynamically consumed by a general query-rewriting engine; the implemented planner supports the project's fixed `ItemHistory` query pattern.

## Phase 2: Entity matching and cleansing under noisy data

The added entity matcher has a different role from schema matching: it identifies likely canonical medicine entities from noisy OCR observations using identifier similarity, contextual fields, and safe ambiguity handling. Raw observations are retained and cleansing outcomes are recorded in an additive audit table.

## Week 4–5: DWH/materialization distinction

The core Part A architecture is virtual/federated rather than loading all source records into one warehouse. Phase 2 creates only a focused observation-resolution/audit table on the scan source; it does not materialize the entire five-source integrated history.
