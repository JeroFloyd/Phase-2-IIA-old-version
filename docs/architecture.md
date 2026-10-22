# Architecture

## Selected architecture
**Mediation / Federated Virtual Integration**.

The implementation follows the course architecture:

Independent SQL databases -> wrappers/connectors -> mediator -> global schema + planner -> federated query -> decomposition/execution -> integrated answer.

The five source databases remain independent. The mediator does not copy all source data into a master database. A user-facing global query is decomposed into source-specific SQL statements, executed against the sources, and integrated at query time.

## Five independent sources

| Source | Local identifier | Main responsibility |
|---|---|---|
| Manufacturer DB | `ProductCode` | manufacturer, product, batch, manufacture/expiry |
| Distributor DB | `SKU` | supplier, vendor, dispatch, quantity |
| Retailer DB | `Barcode` | retail store, purchase date, sale |
| Item Scan DB | `ItemUniqueCode` | consumer scan and observed item description |
| Authority DB | `ReportedCode` | complaint/report, Ministry status, case reference |

## Global mediated relation

`ItemHistory(ItemCode, ProductName, Manufacturer, BatchNo, ManufactureDate, ExpiryDate, Distributor, Vendor, DispatchDate, Quantity, Retailer, RetailCity, PurchaseDate, SalePrice, ScannedName, ScanTimestamp, ScanLocation, ComplaintType, ReportDate, MinistryStatus, CaseReference, EvidenceNote)`

`ItemHistory` is a logical mediated relation used for query reformulation; it is not a centralized physical copy of the five source databases.
