from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class SourceConfig:
    name: str
    host: str
    port: int
    database: str
    item_sql: str

    @property
    def user(self) -> str:
        return os.getenv("DB_USER", "ii_user")

    @property
    def password(self) -> str:
        return os.getenv("DB_PASSWORD", "ii_pass")


SOURCES = {
    "manufacturer": SourceConfig(
        name="Manufacturer DB",
        host=os.getenv("MFG_HOST", "127.0.0.1"),
        port=int(os.getenv("MFG_PORT", "3307")),
        database="manufacturer_db",
        item_sql="""
            SELECT ItemCode, ProductName, Manufacturer, BatchNo,
                   ManufactureDate, ExpiryDate
            FROM manufacturer_item_view
            WHERE ItemCode = %s
            ORDER BY ManufactureDate DESC
            LIMIT 1
        """,
    ),
    "distributor": SourceConfig(
        name="Distributor DB",
        host=os.getenv("DIST_HOST", "127.0.0.1"),
        port=int(os.getenv("DIST_PORT", "3308")),
        database="distributor_db",
        item_sql="""
            SELECT ItemCode, Distributor, Vendor, DispatchDate, Quantity
            FROM distributor_item_view
            WHERE ItemCode = %s
            ORDER BY DispatchDate DESC
            LIMIT 1
        """,
    ),
    "retailer": SourceConfig(
        name="Retailer DB",
        host=os.getenv("RETAIL_HOST", "127.0.0.1"),
        port=int(os.getenv("RETAIL_PORT", "3309")),
        database="retailer_db",
        item_sql="""
            SELECT ItemCode, Retailer, RetailCity, PurchaseDate, SalePrice
            FROM retailer_item_view
            WHERE ItemCode = %s
            ORDER BY PurchaseDate DESC
            LIMIT 1
        """,
    ),
    "item_scan": SourceConfig(
        name="Item Scan DB",
        host=os.getenv("SCAN_HOST", "127.0.0.1"),
        port=int(os.getenv("SCAN_PORT", "3310")),
        database="item_scan_db",
        item_sql="""
            SELECT ItemCode, ScannedName, ScanTimestamp, ScanLocation
            FROM scan_item_view
            WHERE ItemCode = %s
            ORDER BY ScanTimestamp DESC
            LIMIT 1
        """,
    ),
    "authority": SourceConfig(
        name="Authority DB",
        host=os.getenv("AUTH_HOST", "127.0.0.1"),
        port=int(os.getenv("AUTH_PORT", "3311")),
        database="authority_db",
        item_sql="""
            SELECT ItemCode, ComplaintType, ReportDate, MinistryStatus,
                   CaseReference, EvidenceNote
            FROM authority_item_view
            WHERE ItemCode = %s
            ORDER BY ReportDate DESC
            LIMIT 1
        """,
    ),
}
