from __future__ import annotations

import os
import requests
import streamlit as st

from mediator.ocr import extract_label_fields, parse_label_text

API_BASE = os.getenv("MEDIATOR_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = 30

st.set_page_config(page_title="Asali Nakali", page_icon="🔎", layout="wide")
st.title("Asali Nakali — Medicine Verification & Cleansing")
st.caption("Part A: federated integration · Phase 2: OCR-aware entity matching and auditable cleansing")


def api_error(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    return str(detail)


def do_get(path: str, params: dict | None = None) -> dict:
    response = requests.get(f"{API_BASE}{path}", params=params, timeout=REQUEST_TIMEOUT)
    if not response.ok:
        raise RuntimeError(api_error(response))
    return response.json()


def do_post(path: str, payload: dict) -> dict:
    response = requests.post(f"{API_BASE}{path}", json=payload, timeout=REQUEST_TIMEOUT)
    if not response.ok:
        raise RuntimeError(api_error(response))
    return response.json()


with st.sidebar:
    st.subheader("Mediator")
    st.code(API_BASE)
    st.write("Architecture: mediation / federated virtual integration")
    st.write("Canonical candidates are retrieved from the live manufacturer view for each Phase 2 match request.")

part_a_tab, phase2_tab = st.tabs(["Part A — Federated verification", "Phase 2 — Noisy scan & cleansing"])

with part_a_tab:
    st.subheader("Verify a medicine identifier")
    item_code = st.text_input("Enter exact item code", value="MED1001", max_chars=20, key="part_a_item_code").strip().upper()

    if st.button("VERIFY ITEM", type="primary", use_container_width=True, key="part_a_verify"):
        if not item_code or not all(c.isalnum() or c in "_-" for c in item_code):
            st.error("Enter a non-empty item code using letters, numbers, hyphens or underscores.")
        else:
            try:
                with st.spinner("Executing federated query across the five source databases..."):
                    st.session_state["part_a_result"] = do_post(
                        "/query", {"sql": f"SELECT * FROM ItemHistory WHERE ItemCode = '{item_code}';"}
                    )
            except Exception as exc:
                st.error(f"Federated query failed: {exc}")

    result = st.session_state.get("part_a_result")
    if result:
        integrated = result["integrated_result"]
        decision = integrated["decision"]
        if decision == "ASALI":
            st.success("ASALI — required source evidence is present and the authority source explicitly reports NO_ADVERSE_REPORT.")
        elif decision == "NAKALI":
            st.error("NAKALI — the authority source contains a successfully retrieved confirmed report.")
        else:
            st.warning("UNVERIFIED — source evidence is incomplete, under review, or one or more queries failed.")
        st.subheader("Integrated Item History")
        st.dataframe([{
            "Item Code": integrated["item_code"],
            "Product": integrated["product_name"],
            "Manufacturer": integrated["manufacturer"],
            "Batch": integrated["batch_no"],
            "Distributor": integrated["distributor"],
            "Vendor": integrated["vendor"],
            "Retailer": integrated["retailer"],
            "Purchase Date": integrated["purchase_date"],
            "Ministry Status": integrated["ministry_status"],
            "Decision": decision,
        }], use_container_width=True, hide_index=True)
        st.write("**Decision rationale:**", integrated["decision_reason"])
        if integrated.get("source_failures"):
            st.error("Failed source queries: " + ", ".join(integrated["source_failures"]))

        st.subheader("Federation Trace")
        for trace in result["trace"]:
            mark = "✓" if trace["status"] == "success" else "✗"
            st.write(f"{mark} **{trace['source']}** — {trace['rows']} row(s) — {trace['status']}")
            st.code(trace["sql"].replace("%s", repr(trace["parameter"])), language="sql")
            if trace.get("error"):
                st.caption(trace["error"])
        with st.expander("Schema matching evidence"):
            try:
                st.dataframe(do_get("/schema-matches"), use_container_width=True, hide_index=True)
            except Exception as exc:
                st.error(str(exc))
        with st.expander("Raw source results"):
            st.json(result["source_results"])
    else:
        st.info("Try MED1001 (ASALI), MED1002 (NAKALI), MED1008 (UNVERIFIED), or MED9999 (unknown manufacturer).")

with phase2_tab:
    st.subheader("1. Upload and inspect a medicine label")
    st.write("The original OCR text is preserved. Extracted fields can be reviewed before matching; the matcher does not silently rewrite the original observation.")
    uploaded = st.file_uploader("Medicine-label image (PNG/JPG/JPEG)", type=["png", "jpg", "jpeg"], key="phase2_image")
    if uploaded is not None:
        st.image(uploaded, caption=f"Uploaded image: {uploaded.name}", use_container_width=True)
    if "p2_raw_ocr_text" not in st.session_state:
        st.session_state["p2_raw_ocr_text"] = ""
    for key in ("p2_code", "p2_product", "p2_batch", "p2_manufacturer", "p2_expiry"):
        st.session_state.setdefault(key, "")

    if st.button("EXTRACT TEXT WITH OCR", type="primary", disabled=uploaded is None, key="phase2_ocr"):
        try:
            parsed = extract_label_fields(uploaded.getvalue())
            st.session_state["p2_raw_ocr_text"] = parsed.get("raw_ocr_text", "")
            st.session_state["p2_code"] = parsed.get("observed_item_code") or ""
            st.session_state["p2_product"] = parsed.get("observed_product_name") or ""
            st.session_state["p2_batch"] = parsed.get("observed_batch_no") or ""
            st.session_state["p2_manufacturer"] = parsed.get("observed_manufacturer") or ""
            st.session_state["p2_expiry"] = parsed.get("observed_expiry_date") or ""
            st.success("OCR finished. Review each extracted field below before matching.")
        except Exception as exc:
            st.error(f"OCR was not available or could not read this image: {exc}")
            st.info("You can still demonstrate the matcher by typing the noisy OCR output and contextual fields below. The text you enter is treated as observed text, not as proof of successful image OCR.")

    st.text_area("Raw OCR text (retained as provenance)", key="p2_raw_ocr_text", height=120,
                 help="This should show the OCR output. You may edit it to record a corrected transcription, but keep the actual OCR output available for a faithful evaluation.")
    st.caption("Review the fields that will be sent to the matcher:")
    c1, c2 = st.columns(2)
    with c1:
        observed_code = st.text_input("Observed / noisy item code", key="p2_code", max_chars=40)
        observed_product = st.text_input("Observed product name", key="p2_product", max_chars=150)
        observed_batch = st.text_input("Observed batch number", key="p2_batch", max_chars=50)
    with c2:
        observed_manufacturer = st.text_input("Observed manufacturer", key="p2_manufacturer", max_chars=150)
        observed_expiry = st.text_input("Observed expiry date", key="p2_expiry", max_chars=30,
                                        help="Enter the readable date as it appears on the label, e.g. 2028-01-11.")

    payload = {
        "raw_ocr_text": st.session_state["p2_raw_ocr_text"],
        "observed_item_code": observed_code.strip(),
        "observed_product_name": observed_product.strip() or None,
        "observed_batch_no": observed_batch.strip() or None,
        "observed_manufacturer": observed_manufacturer.strip() or None,
        "observed_expiry_date": observed_expiry.strip() or None,
        "image_filename": uploaded.name if uploaded is not None else None,
    }

    if st.button("FIND APPROXIMATE MATCHES", type="primary", use_container_width=True, key="phase2_match"):
        if not payload["observed_item_code"]:
            st.error("Enter or extract an observed item code first.")
        else:
            try:
                with st.spinner("Reading the current manufacturer catalogue and scoring candidates..."):
                    st.session_state["phase2_match_result"] = do_post("/phase2/match", payload)
                    st.session_state["phase2_last_payload"] = payload
            except Exception as exc:
                st.error(f"Entity matching failed: {exc}")

    match_result = st.session_state.get("phase2_match_result")
    current_match_is_stale = st.session_state.get("phase2_last_payload") != payload
    if match_result:
        if current_match_is_stale:
            st.warning("The extracted fields changed after the last match. Run FIND APPROXIMATE MATCHES again before saving a decision.")
        st.subheader("2. Ranked canonical candidates")
        status = match_result.get("match_status", "NEEDS_REVIEW")
        if status == "AUTO_MATCHED":
            st.success(f"Automatic recommendation: {match_result.get('suggested_item_code')} (score {match_result.get('suggested_score')})")
        elif status == "NEEDS_REVIEW":
            st.warning(f"Human review required. Best candidate: {match_result.get('top_candidate_item_code')} (score {match_result.get('suggested_score')})")
        else:
            st.error("No sufficiently supported canonical match was found.")
        st.write("**Reason:**", match_result.get("reason"))
        st.caption(f"Live catalogue rows queried: {match_result.get('catalogue_count')} · Source: {match_result.get('catalogue_source')}")
        st.dataframe(match_result.get("candidates", []), use_container_width=True, hide_index=True)

        st.subheader("3. Save an auditable cleansing decision")
        st.write("Automatic decisions are saved only when safeguards pass. Otherwise a review record is saved without assigning a canonical code unless you explicitly approve a listed candidate.")
        candidate_codes = [row.get("item_code", "") for row in match_result.get("candidates", []) if row.get("item_code")]
        review_mode = st.radio(
            "Resolution mode",
            ["Save algorithm decision (do not force a match)", "I have reviewed and approve a candidate"],
            horizontal=False,
            key="p2_resolution_mode",
        )
        selected_code = None
        human_approved = review_mode == "I have reviewed and approve a candidate"
        if human_approved:
            if candidate_codes:
                suggested = match_result.get("top_candidate_item_code") or candidate_codes[0]
                default_index = candidate_codes.index(suggested) if suggested in candidate_codes else 0
                selected_code = st.selectbox("Candidate to approve", candidate_codes, index=default_index, key="p2_selected_canonical")
                st.warning("Only approve after checking the displayed code/context evidence. A human approval is explicitly recorded in the audit row.")
            else:
                st.error("There are no candidates to approve.")

        if st.button("SAVE CLEANSING AUDIT RECORD", use_container_width=True, key="phase2_save", disabled=current_match_is_stale):
            if not payload["observed_item_code"]:
                st.error("Enter or extract an observed item code first.")
            elif human_approved and not selected_code:
                st.error("There is no candidate to approve.")
            else:
                save_payload = {
                    **payload,
                    "selected_item_code": selected_code if human_approved else None,
                    "human_approved": human_approved,
                }
                try:
                    with st.spinner("Rechecking against live data and saving the resolution record..."):
                        saved = do_post("/phase2/cleanse", save_payload)
                    st.session_state["phase2_saved_result"] = saved
                except Exception as exc:
                    st.error(f"Could not save the resolution. Check migration/permissions and the remote source connection: {exc}")

    saved_result = st.session_state.get("phase2_saved_result")
    if saved_result:
        st.success(f"Saved resolution #{saved_result.get('resolution_id')}: {saved_result.get('match_status')}")
        st.json({k: v for k, v in saved_result.items() if k != "matching_result"})
        if saved_result.get("canonical_item_code"):
            st.info(f"Canonical code recorded: {saved_result['canonical_item_code']}. Use Part A's tab to retrieve the integrated history for this code.")
        else:
            st.info("No canonical code was assigned by the algorithm. The observation remains available for review.")

    st.divider()
    st.subheader("4. Reverse match: canonical medicine → noisy observations")
    st.write("This searches the live item_scan rows and, when the Phase 2 table has been migrated and permissioned, previously recorded Phase 2 observations.")
    reverse_code = st.text_input("Canonical medicine code", value="MED1002", max_chars=20, key="p2_reverse_code").strip().upper()
    if st.button("FIND APPROXIMATELY MATCHING SCANS", key="p2_reverse_match"):
        if not reverse_code:
            st.error("Enter a canonical code.")
        else:
            try:
                st.session_state["p2_reverse_result"] = do_get(f"/phase2/reverse-match/{reverse_code}")
            except Exception as exc:
                st.error(f"Reverse matching failed: {exc}")
    reverse_result = st.session_state.get("p2_reverse_result")
    if reverse_result:
        st.caption(f"Canonical medicine: {reverse_result['canonical_item_code']} · Approximately matching observations: {reverse_result['count']}")
        for warning in reverse_result.get("warnings", []):
            st.warning(warning)
        st.dataframe(reverse_result.get("candidate_observations", []), use_container_width=True, hide_index=True)

    st.divider()
    with st.expander("Algorithm settings and rationale"):
        try:
            st.json(do_get("/phase2/algorithm-info"))
        except Exception as exc:
            st.error(str(exc))
    if st.button("LOAD RECENT CLEANSING AUDIT RECORDS", key="p2_load_audit"):
        try:
            st.session_state["p2_audit_records"] = do_get("/phase2/resolutions", params={"limit": 20})
        except Exception as exc:
            st.error(f"Audit table not ready: {exc}")
            st.info("Run databases/item_scan/04_phase2_resolution.sql on the teammate's MySQL server and apply the read/insert grant documented in docs/phase2_database_setup.md.")
    if "p2_audit_records" in st.session_state:
        audit = st.session_state["p2_audit_records"]
        st.write(f"Recent saved records: {audit['count']}")
        st.dataframe(audit["records"], use_container_width=True, hide_index=True)
