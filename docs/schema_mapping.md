# Schema Matching and Source-to-Global Mapping

## Why matching is necessary

The independently designed source schemas use different names for comparable concepts. Examples include:

- `ProductCode`, `SKU`, `Barcode`, `ItemUniqueCode`, `ReportedCode` -> global `ItemCode`
- `manufacturer_company.legal_name` -> global `Manufacturer`
- `supplier.supplier_name` -> global `Distributor`
- `retail_store.store_name` -> global `Retailer`
- `MfgDate` -> global `ManufactureDate`

## Attribute matcher

`mediator/schema_matcher.py` combines declared domain aliases with lexical similarity for other attributes. `GET /schema-matches` exposes the local attribute, global attribute, score, acceptance and rule. The lexical score reports string similarity; alias acceptance is a separate semantic rule.

## How mapping is executed in the current Part A code

`mediator/mappings.py` is a declarative reference dictionary. It is **not dynamically executed** by the current query planner. In the runtime, each source's SQL view (for example `manufacturer_item_view`) normalizes local columns and joins local relationship tables; `mediator/config.py` then defines the parameterized source query against that view. `query_decomposer.py` selects these fixed source-specific queries and pushes the same ItemCode predicate to every source.

This is a simple predefined GAV-style mapping for the project scope, rather than a general mapping compiler that can rewrite arbitrary SQL. This scope should be described accurately in the viva.
