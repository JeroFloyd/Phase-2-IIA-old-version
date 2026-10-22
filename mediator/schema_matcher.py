from __future__ import annotations

from dataclasses import dataclass
from rapidfuzz.fuzz import ratio


@dataclass(frozen=True)
class Match:
    source: str
    local_attribute: str
    global_attribute: str | None
    lexical_similarity: float
    accepted: bool
    rule: str


GLOBAL_ATTRIBUTES = [
    "ItemCode", "ProductName", "Manufacturer", "BatchNo", "ManufactureDate",
    "ExpiryDate", "Distributor", "Vendor", "DispatchDate", "Quantity",
    "Retailer", "RetailCity", "PurchaseDate", "SalePrice", "ScannedName",
    "ScanTimestamp", "ScanLocation", "ComplaintType", "ReportDate",
    "MinistryStatus", "CaseReference", "EvidenceNote",
]

SOURCES = {
    "manufacturer": [
        "ProductCode", "ProductName", "manufacturer_id", "legal_name", "BatchNo", "MfgDate", "ExpiryDate"
    ],
    "distributor": [
        "shipment_id", "SKU", "supplier_name", "VendorName", "DispatchDate", "Quantity"
    ],
    "retailer": [
        "SaleId", "Barcode", "store_name", "city", "PurchaseDate", "SalePrice"
    ],
    "item_scan": [
        "ScanId", "ItemUniqueCode", "ScannedName", "ScanTimestamp", "ScanLocation"
    ],
    "authority": [
        "ReportId", "ReportedCode", "ComplaintType", "ReportDate",
        "MinistryStatus", "CaseReference", "EvidenceNote"
    ],
}

ALIASES = {
    "ProductCode": "ItemCode", "SKU": "ItemCode", "Barcode": "ItemCode",
    "ItemUniqueCode": "ItemCode", "ReportedCode": "ItemCode",
    "legal_name": "Manufacturer", "supplier_name": "Distributor",
    "VendorName": "Vendor", "MfgDate": "ManufactureDate", "store_name": "Retailer",
    "city": "RetailCity",
}


def match_source(source: str, threshold: float = 0.78) -> list[Match]:
    result: list[Match] = []
    for local in SOURCES[source]:
        if local in ALIASES:
            result.append(Match(source, local, ALIASES[local], round(ratio(local.lower(), ALIASES[local].lower()) / 100.0, 3), True, "domain alias"))
            continue
        if local.lower().endswith("id") and local.lower() not in {"itemuniqueid", "productid"}:
            result.append(Match(source, local, None, 0.0, False, "source-local key not exposed in global view"))
            continue
        best_global = max(GLOBAL_ATTRIBUTES, key=lambda g: ratio(local.lower(), g.lower()) / 100.0)
        score = ratio(local.lower(), best_global.lower()) / 100.0
        result.append(Match(source, local, best_global, round(score, 3), score >= threshold, "lexical similarity"))
    return result


def all_matches() -> list[dict]:
    rows: list[dict] = []
    for source in SOURCES:
        for match in match_source(source):
            rows.append(match.__dict__)
    return rows
