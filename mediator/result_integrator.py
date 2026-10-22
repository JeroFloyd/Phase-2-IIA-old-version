from __future__ import annotations

from typing import Any


def integrate(
    item_code: str,
    source_results: dict[str, list[dict[str, Any]]],
    source_status: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Integrate source rows while treating failed/missing authority evidence cautiously.

    An absent authority row is not equivalent to an explicit NO_ADVERSE_REPORT.
    A failed source query is not equivalent to a source that successfully returned
    zero rows. Only explicit, successful source evidence supports ASALI/NAKALI.
    """
    source_status = source_status or {}
    manufacturer = source_results.get("manufacturer", [{}])[0] if source_results.get("manufacturer") else {}
    distributor = source_results.get("distributor", [{}])[0] if source_results.get("distributor") else {}
    retailer = source_results.get("retailer", [{}])[0] if source_results.get("retailer") else {}
    scan = source_results.get("item_scan", [{}])[0] if source_results.get("item_scan") else {}
    authority = source_results.get("authority", [{}])[0] if source_results.get("authority") else {}

    authority_status = authority.get("MinistryStatus")
    required_keys = ("manufacturer", "distributor", "retailer", "item_scan", "authority")
    failed_sources = [key for key in required_keys if source_status.get(key, "success") != "success"]
    manufacturer_exists = bool(manufacturer)
    distributor_exists = bool(distributor)
    retailer_exists = bool(retailer)
    scan_exists = bool(scan)

    if "authority" in failed_sources:
        decision = "UNVERIFIED"
        reason = "The authority source could not be queried successfully; absence of a report cannot be inferred."
    elif authority_status == "CONFIRMED_NAKALI":
        decision = "NAKALI"
        reason = "The authority source contains a successfully retrieved CONFIRMED_NAKALI record."
    elif authority_status == "UNDER_REVIEW":
        decision = "UNVERIFIED"
        reason = "The authority source marks this item UNDER_REVIEW."
    elif authority_status != "NO_ADVERSE_REPORT":
        decision = "UNVERIFIED"
        reason = "No explicit NO_ADVERSE_REPORT or CONFIRMED_NAKALI authority status was retrieved."
    elif failed_sources:
        decision = "UNVERIFIED"
        reason = "One or more source queries failed: " + ", ".join(failed_sources) + "."
    elif manufacturer_exists and distributor_exists and retailer_exists and scan_exists:
        decision = "ASALI"
        reason = "Manufacturer, distributor, retailer and scan evidence are present, and the authority source explicitly reports NO_ADVERSE_REPORT."
    else:
        decision = "UNVERIFIED"
        missing = []
        if not manufacturer_exists:
            missing.append("manufacturer")
        if not distributor_exists:
            missing.append("distributor")
        if not retailer_exists:
            missing.append("retailer")
        if not scan_exists:
            missing.append("scan")
        reason = "Required source evidence is incomplete: " + ", ".join(missing) + "."

    return {
        "item_code": item_code,
        "product_name": manufacturer.get("ProductName") or scan.get("ScannedName"),
        "manufacturer": manufacturer.get("Manufacturer"),
        "batch_no": manufacturer.get("BatchNo"),
        "manufacture_date": manufacturer.get("ManufactureDate"),
        "expiry_date": manufacturer.get("ExpiryDate"),
        "distributor": distributor.get("Distributor"),
        "vendor": distributor.get("Vendor"),
        "dispatch_date": distributor.get("DispatchDate"),
        "quantity": distributor.get("Quantity"),
        "retailer": retailer.get("Retailer"),
        "retail_city": retailer.get("RetailCity"),
        "purchase_date": retailer.get("PurchaseDate"),
        "sale_price": retailer.get("SalePrice"),
        "scan_timestamp": scan.get("ScanTimestamp"),
        "scan_location": scan.get("ScanLocation"),
        "ministry_status": authority_status,
        "case_reference": authority.get("CaseReference"),
        "complaint_type": authority.get("ComplaintType"),
        "evidence_note": authority.get("EvidenceNote"),
        "decision": decision,
        "decision_reason": reason,
        "source_failures": failed_sources,
    }
