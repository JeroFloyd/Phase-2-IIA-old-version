from __future__ import annotations

# Declarative reference correspondences between source-local attributes and the
# mediated schema. In the current Part A runtime, source views and the constant
# queries in config.py perform the executable normalization; this dictionary is
# explanatory metadata and is not itself consumed by the query planner.
GAV_MAPPINGS = {
    "manufacturer": {
        "ItemCode": "ProductCode",
        "ProductName": "ProductName",
        "Manufacturer": "manufacturer_company.legal_name",
        "BatchNo": "BatchNo",
        "ManufactureDate": "MfgDate",
        "ExpiryDate": "ExpiryDate",
    },
    "distributor": {
        "ItemCode": "SKU",
        "Distributor": "supplier.supplier_name",
        "Vendor": "VendorName",
        "DispatchDate": "DispatchDate",
        "Quantity": "Quantity",
    },
    "retailer": {
        "ItemCode": "Barcode",
        "Retailer": "retail_store.store_name",
        "RetailCity": "retail_store.city",
        "PurchaseDate": "PurchaseDate",
        "SalePrice": "SalePrice",
    },
    "item_scan": {
        "ItemCode": "ItemUniqueCode",
        "ScannedName": "ScannedName",
        "ScanTimestamp": "ScanTimestamp",
        "ScanLocation": "ScanLocation",
    },
    "authority": {
        "ItemCode": "ReportedCode",
        "ComplaintType": "ComplaintType",
        "ReportDate": "ReportDate",
        "MinistryStatus": "MinistryStatus",
        "CaseReference": "CaseReference",
        "EvidenceNote": "EvidenceNote",
    },
}
