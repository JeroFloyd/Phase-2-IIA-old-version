from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import SOURCES
from .connections import execute_write, fetch_one, fetch_rows
from .entity_matcher import match_candidates, score_observation_against_canonical, WEIGHTS, AUTO_MATCH_SCORE, AUTO_MATCH_MARGIN
from .query_decomposer import decompose_item_history_query
from .result_integrator import integrate
from .schema_matcher import all_matches

app = FastAPI(
    title="Asali Nakali Information Integration Mediator",
    version="2.0.0",
    description="Federated integration across five MySQL sources, with noisy medicine entity matching and auditable cleansing.",
)


class SQLQueryRequest(BaseModel):
    sql: str


class NoisyObservation(BaseModel):
    raw_ocr_text: str = Field(default="", max_length=12000)
    observed_item_code: str = Field(min_length=1, max_length=40)
    observed_product_name: str | None = Field(default=None, max_length=150)
    observed_batch_no: str | None = Field(default=None, max_length=50)
    observed_manufacturer: str | None = Field(default=None, max_length=150)
    observed_expiry_date: str | None = Field(default=None, max_length=30)
    image_filename: str | None = Field(default=None, max_length=255)


class CleanseRequest(NoisyObservation):
    selected_item_code: str | None = Field(default=None, max_length=20)
    human_approved: bool = False


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    return value


def _canonical_candidates() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Read the canonical catalogue on every request so inserts/updates are visible.
    return fetch_rows(
        SOURCES["manufacturer"],
        """
        SELECT ItemCode, ProductName, Manufacturer, BatchNo, ManufactureDate, ExpiryDate
        FROM manufacturer_item_view
        ORDER BY ItemCode
        """,
    )


def _observation_payload(request: NoisyObservation) -> dict[str, Any]:
    return {
        "raw_ocr_text": request.raw_ocr_text,
        "observed_item_code": request.observed_item_code,
        "observed_product_name": request.observed_product_name,
        "observed_batch_no": request.observed_batch_no,
        "observed_manufacturer": request.observed_manufacturer,
        "observed_expiry_date": request.observed_expiry_date,
        "image_filename": request.image_filename,
    }


def _source_error(meta: dict[str, Any], label: str) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=f"{label} is unavailable ({meta.get('status')}): {meta.get('error', 'no details')}",
    )


@app.get("/health")
def health() -> dict[str, Any]:
    statuses = {}
    for key, config in SOURCES.items():
        _, meta = fetch_one(config, "__health_probe__")
        statuses[key] = {k: jsonable(v) for k, v in meta.items() if k != "rows"}
    return {"mediator": "ok", "sources": statuses}


@app.get("/schema-matches")
def schema_matches() -> list[dict[str, Any]]:
    return all_matches()


@app.get("/plan")
def query_plan(item_code: str = Query(..., min_length=1, max_length=20)) -> dict[str, Any]:
    return {"global_query": "SELECT * FROM ItemHistory WHERE ItemCode = ?", "subqueries": decompose_item_history_query(item_code)}


@app.post("/query")
def federated_sql(request: SQLQueryRequest) -> dict[str, Any]:
    """Execute the supported global SQL form through federation.

    Supported form:
      SELECT * FROM ItemHistory WHERE ItemCode = 'MED1001';
    """
    sql = request.sql.strip().rstrip(";").strip()
    pattern = re.compile(
        r"^SELECT\s+\*\s+FROM\s+ItemHistory\s+WHERE\s+ItemCode\s*=\s*['\"]([A-Za-z0-9_-]+)['\"]$",
        re.IGNORECASE,
    )
    match = pattern.match(sql)
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Only SELECT * FROM ItemHistory WHERE ItemCode = 'VALUE' is supported in Part A.",
        )
    return verify_item(match.group(1))


@app.get("/verify/{item_code}")
def verify_item(item_code: str) -> dict[str, Any]:
    item_code = item_code.strip().upper()
    if not item_code:
        raise HTTPException(status_code=400, detail="Item code cannot be empty")

    plan = decompose_item_history_query(item_code)
    source_results: dict[str, list[dict[str, Any]]] = {}
    source_status: dict[str, str] = {}
    trace = []

    for step in plan:
        key = step["source_key"]
        rows, meta = fetch_one(SOURCES[key], item_code)
        source_results[key] = rows
        source_status[key] = meta["status"]
        trace.append({
            "source": meta["source"],
            "database": meta["database"],
            "status": meta["status"],
            "rows": meta["rows"],
            "sql": step["sql"],
            "parameter": item_code,
            "error": meta.get("error"),
        })

    integrated = integrate(item_code, source_results, source_status)
    return jsonable({
        "global_query": f"SELECT * FROM ItemHistory WHERE ItemCode = '{item_code}';",
        "decomposition": plan,
        "source_results": source_results,
        "integrated_result": integrated,
        "trace": trace,
    })


@app.get("/phase2/algorithm-info")
def phase2_algorithm_info() -> dict[str, Any]:
    return {
        "algorithm": "OCR-aware identifier similarity + weighted contextual matching + ambiguity/conflict guard",
        "weights": WEIGHTS,
        "automatic_match_threshold": AUTO_MATCH_SCORE,
        "minimum_top_two_margin": AUTO_MATCH_MARGIN,
        "principles": [
            "Candidate records are fetched from the live manufacturer view for each request.",
            "Identifier normalization is conservative and retains the original observed code.",
            "Available context is compared; missing context is not treated as a mismatch.",
            "Known batch or parseable expiry conflicts block automatic correction.",
            "Ambiguous or weak cases are flagged for review rather than silently corrected.",
        ],
        "note": "These are initial configurable settings. Use the included labelled synthetic evaluation to compare exact, fuzzy-only, and hybrid approaches before claiming best accuracy.",
    }


@app.post("/phase2/match")
def phase2_match(request: NoisyObservation) -> dict[str, Any]:
    candidates, meta = _canonical_candidates()
    if meta["status"] != "success":
        raise _source_error(meta, "Manufacturer candidate catalogue")
    result = match_candidates(_observation_payload(request), candidates)
    return jsonable({
        **result,
        "catalogue_count": len(candidates),
        "catalogue_source": meta["database"],
        "catalogue_fetched_live": True,
    })


@app.post("/phase2/cleanse")
def phase2_cleanse(request: CleanseRequest) -> dict[str, Any]:
    """Run matching and persist the raw observation plus a safe resolution decision."""
    candidates, meta = _canonical_candidates()
    if meta["status"] != "success":
        raise _source_error(meta, "Manufacturer candidate catalogue")

    observation = _observation_payload(request)
    match = match_candidates(observation, candidates)
    selected_code = (request.selected_item_code or "").strip().upper()
    canonical_code = None
    final_status = match["match_status"]
    score = match.get("suggested_score")
    reason = match["reason"]

    if request.human_approved:
        if not selected_code:
            raise HTTPException(status_code=400, detail="Select a candidate code before marking it manually approved.")
        selected = next((c for c in match["candidates"] if c["item_code"].upper() == selected_code), None)
        if selected is None:
            raise HTTPException(status_code=400, detail="The selected code is not among the live ranked candidates. Run matching again and choose a listed candidate.")
        canonical_code = selected["item_code"]
        score = selected["final_score"]
        final_status = "MANUALLY_APPROVED"
        reason = f"Human reviewed and approved {canonical_code}. Algorithm recommendation: {match['match_status']} — {match['reason']}"
    elif match["match_status"] == "AUTO_MATCHED":
        canonical_code = match["suggested_item_code"]

    sql = """
        INSERT INTO phase2_observation_resolution
        (RawImageName, RawOCRText, ObservedItemCode, ObservedProductName,
         ObservedBatchNo, ObservedManufacturer, ObservedExpiryDate,
         CanonicalItemCode, MatchScore, MatchStatus, MatchReason, IsHumanApproved)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        request.image_filename,
        request.raw_ocr_text,
        request.observed_item_code.strip().upper(),
        request.observed_product_name,
        request.observed_batch_no,
        request.observed_manufacturer,
        request.observed_expiry_date,
        canonical_code,
        score,
        final_status,
        reason,
        bool(request.human_approved),
    )
    saved = execute_write(SOURCES["item_scan"], sql, params)
    if saved["status"] != "success":
        raise HTTPException(
            status_code=503,
            detail=("Could not save the cleansing audit record. On the teammate's MySQL server, execute "
                    "databases/item_scan/04_phase2_resolution.sql and the narrowly scoped GRANT in "
                    "docs/phase2_database_setup.md. Database error: " + saved.get("error", "unknown error")),
        )
    return jsonable({
        "resolution_id": saved.get("lastrowid"),
        "observed_item_code": request.observed_item_code.strip().upper(),
        "canonical_item_code": canonical_code,
        "match_score": score,
        "match_status": final_status,
        "match_reason": reason,
        "human_approved": bool(request.human_approved),
        "matching_result": match,
        "persistence": "saved to item_scan_db.phase2_observation_resolution",
    })


@app.get("/phase2/resolutions")
def phase2_resolutions(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    rows, meta = fetch_rows(
        SOURCES["item_scan"],
        """
        SELECT ResolutionId, RawImageName, RawOCRText, ObservedItemCode,
               ObservedProductName, ObservedBatchNo, ObservedManufacturer,
               ObservedExpiryDate, CanonicalItemCode, MatchScore, MatchStatus,
               MatchReason, IsHumanApproved, CreatedAt, UpdatedAt
        FROM phase2_observation_resolution
        ORDER BY CreatedAt DESC, ResolutionId DESC
        LIMIT %s
        """,
        (limit,),
    )
    if meta["status"] != "success":
        raise _source_error(meta, "Phase 2 resolution table (run the Phase 2 migration and permissions script)")
    return jsonable({"source": meta["database"], "count": len(rows), "records": rows})


@app.get("/phase2/reverse-match/{canonical_item_code}")
def phase2_reverse_match(canonical_item_code: str) -> dict[str, Any]:
    """Find approximate existing scan observations for a canonical medicine code."""
    requested = canonical_item_code.strip().upper()
    if not requested:
        raise HTTPException(status_code=400, detail="Canonical item code cannot be empty")

    catalogue, meta = _canonical_candidates()
    if meta["status"] != "success":
        raise _source_error(meta, "Manufacturer candidate catalogue")
    canonical = next((row for row in catalogue if str(row.get("ItemCode", "")).upper() == requested), None)
    if canonical is None:
        raise HTTPException(status_code=404, detail=f"Canonical medicine {requested} was not found in the live manufacturer catalogue.")

    base_rows, scan_meta = fetch_rows(
        SOURCES["item_scan"],
        """
        SELECT ScanId, ItemUniqueCode, ScannedName, ScanTimestamp, ScanLocation
        FROM item_scan
        ORDER BY ScanTimestamp DESC
        """,
    )
    if scan_meta["status"] != "success":
        raise _source_error(scan_meta, "Item Scan source")

    observations: list[dict[str, Any]] = []
    for row in base_rows:
        scored = score_observation_against_canonical(row, canonical)
        if scored["code_similarity"] >= 40:
            observations.append({
                "observation_type": "existing_scan",
                "observation_id": row.get("ScanId"),
                "observed_item_code": row.get("ItemUniqueCode"),
                "observed_product_name": row.get("ScannedName"),
                "scan_timestamp": row.get("ScanTimestamp"),
                "scan_location": row.get("ScanLocation"),
                "code_similarity": scored["code_similarity"],
                "product_name_similarity": scored["product_name_similarity"],
                "final_score": scored["final_score"],
                "context_conflicts": scored["context_conflicts"],
            })

    warnings = []
    resolution_rows, resolution_meta = fetch_rows(
        SOURCES["item_scan"],
        """
        SELECT ResolutionId, ObservedItemCode, ObservedProductName, ObservedBatchNo,
               ObservedManufacturer, ObservedExpiryDate, MatchStatus, CanonicalItemCode,
               MatchScore, CreatedAt
        FROM phase2_observation_resolution
        ORDER BY CreatedAt DESC
        LIMIT 500
        """,
    )
    if resolution_meta["status"] == "success":
        for row in resolution_rows:
            scored = score_observation_against_canonical(row, canonical)
            if scored["code_similarity"] >= 40:
                observations.append({
                    "observation_type": "phase2_resolution",
                    "observation_id": row.get("ResolutionId"),
                    "observed_item_code": row.get("ObservedItemCode"),
                    "observed_product_name": row.get("ObservedProductName"),
                    "previous_match_status": row.get("MatchStatus"),
                    "previous_canonical_code": row.get("CanonicalItemCode"),
                    "previous_match_score": row.get("MatchScore"),
                    "created_at": row.get("CreatedAt"),
                    "code_similarity": scored["code_similarity"],
                    "product_name_similarity": scored["product_name_similarity"],
                    "final_score": scored["final_score"],
                    "context_conflicts": scored["context_conflicts"],
                })
    else:
        warnings.append("The optional Phase 2 resolution table is not readable yet; only existing item_scan rows were searched.")

    observations.sort(key=lambda row: (row["final_score"], row["code_similarity"]), reverse=True)
    return jsonable({
        "canonical_item_code": requested,
        "canonical_record": canonical,
        "matching_direction": "canonical medicine -> approximately matching noisy scan observations",
        "candidate_observations": observations,
        "count": len(observations),
        "source_read_live": True,
        "warnings": warnings,
    })
