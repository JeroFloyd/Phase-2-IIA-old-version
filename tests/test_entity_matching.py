import unittest

from mediator.entity_matcher import match_candidates, ocr_normalize_identifier, score_observation_against_canonical
from mediator.ocr import parse_label_text
from mediator.result_integrator import integrate


CANDIDATES = [
    {"ItemCode": "MED1001", "ProductName": "Paracetamol 500 mg Tablet", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24P01", "ExpiryDate": "2028-01-09"},
    {"ItemCode": "MED1002", "ProductName": "Paracetamol 500 mg Tablet", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24P02", "ExpiryDate": "2028-01-11"},
    {"ItemCode": "MED1003", "ProductName": "Azithromycin 250 mg Tablet", "Manufacturer": "Bharat Health Labs", "BatchNo": "BH24A11", "ExpiryDate": "2028-02-04"},
    {"ItemCode": "MED1004", "ProductName": "Pantoprazole 40 mg Tablet", "Manufacturer": "CureNova Pharmaceuticals", "BatchNo": "CN24T09", "ExpiryDate": "2028-02-17"},
    {"ItemCode": "MED1005", "ProductName": "Cetirizine 10 mg Tablet", "Manufacturer": "Bharat Health Labs", "BatchNo": "BH24C22", "ExpiryDate": "2028-03-01"},
    {"ItemCode": "MED1006", "ProductName": "Amoxicillin 500 mg Capsule", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24M18", "ExpiryDate": "2028-03-10"},
    {"ItemCode": "MED1007", "ProductName": "ORS Powder Sachet", "Manufacturer": "CureNova Pharmaceuticals", "BatchNo": "CN24O12", "ExpiryDate": "2028-03-18"},
    {"ItemCode": "MED1008", "ProductName": "Ibuprofen 400 mg Tablet", "Manufacturer": "Apex Lifesciences Pvt Ltd", "BatchNo": "AX24I07", "ExpiryDate": "2028-03-31"},
]


class EntityMatchingTests(unittest.TestCase):
    def observation(self, code, name=None, batch=None, manufacturer=None, expiry=None):
        return {
            "observed_item_code": code,
            "observed_product_name": name,
            "observed_batch_no": batch,
            "observed_manufacturer": manufacturer,
            "observed_expiry_date": expiry,
        }

    def test_ocr_numeric_suffix_normalization(self):
        self.assertEqual(ocr_normalize_identifier("MED1OO2"), "MED1002")

    def test_context_corroborates_ocr_noisy_identifier(self):
        result = match_candidates(self.observation(
            "MED1OO2", "Paracetamol 500 mg Tablet", "AX24P02",
            "Apex Lifesciences Pvt Ltd", "2028-01-11"
        ), CANDIDATES)
        self.assertEqual(result["top_candidate_item_code"], "MED1002")
        self.assertEqual(result["match_status"], "AUTO_MATCHED")
        self.assertEqual(result["suggested_item_code"], "MED1002")

    def test_context_disambiguates_close_codes(self):
        result = match_candidates(self.observation(
            "MED100Z", "ORS Powder Sachet", "CN24O12",
            "CureNova Pharmaceuticals", "2028-03-18"
        ), CANDIDATES)
        self.assertEqual(result["top_candidate_item_code"], "MED1007")
        self.assertEqual(result["match_status"], "AUTO_MATCHED")

    def test_batch_number_ocr_confusion_is_handled_conservatively(self):
        result = match_candidates(self.observation(
            "MED100Z", "ORS Powder Sachet", "CN24012",
            "CureNova Pharmaceuticals", "2028-03-18"
        ), CANDIDATES)
        self.assertEqual(result["top_candidate_item_code"], "MED1007")
        self.assertEqual(result["match_status"], "AUTO_MATCHED")
        self.assertTrue(result["candidates"][0]["batch_ocr_normalization_helped"])

    def test_explicit_batch_conflict_prevents_automatic_correction(self):
        result = match_candidates(self.observation(
            "MED1001", "Paracetamol 500 mg Tablet", "AX24P02",
            "Apex Lifesciences Pvt Ltd", "2028-01-11"
        ), CANDIDATES)
        self.assertEqual(result["top_candidate_item_code"], "MED1002")
        self.assertEqual(result["match_status"], "NEEDS_REVIEW")
        self.assertIsNone(result["suggested_item_code"])

    def test_exact_identifier_with_conflicting_product_context_needs_review(self):
        result = match_candidates(self.observation(
            "MED1001", "Ibuprofen 400 mg Tablet", None,
            "Apex Lifesciences Pvt Ltd", None
        ), CANDIDATES)
        self.assertNotEqual(result["match_status"], "AUTO_MATCHED")
        self.assertIsNone(result["suggested_item_code"])

    def test_unknown_identifier_is_not_auto_assigned(self):
        result = match_candidates(self.observation(
            "MED7777", "Mystery product", "ZZ99ZZ", "Unknown Manufacturer", "2029-12-31"
        ), CANDIDATES)
        self.assertEqual(result["match_status"], "NO_MATCH")
        self.assertIsNone(result["suggested_item_code"])

    def test_no_context_does_not_auto_correct_noisy_code(self):
        result = match_candidates(self.observation("MED100Z"), CANDIDATES)
        self.assertNotEqual(result["match_status"], "AUTO_MATCHED")
        self.assertIsNone(result["suggested_item_code"])

    def test_reverse_direction_scores_noisy_scan_against_canonical(self):
        scan_row = {"ScanId": 9911, "ItemUniqueCode": "MED100Z", "ScannedName": "ORS Powder Sachet"}
        canonical = next(row for row in CANDIDATES if row["ItemCode"] == "MED1007")
        result = score_observation_against_canonical(scan_row, canonical)
        self.assertEqual(result["code_similarity"], 85.71)
        self.assertEqual(result["product_name_similarity"], 100.0)
        self.assertGreater(result["final_score"], 85.0)

    def test_label_parser_extracts_labelled_fields(self):
        parsed = parse_label_text("""ITEM CODE: MED1OO2
PRODUCT NAME: Paracetamol 500 mg Tablet
BATCH NO: AX24P02
MANUFACTURER: Apex Lifesciences Pvt Ltd
EXPIRY DATE: 2028-01-11""")
        self.assertEqual(parsed["observed_item_code"], "MED1OO2")
        self.assertEqual(parsed["observed_product_name"], "Paracetamol 500 mg Tablet")
        self.assertEqual(parsed["observed_batch_no"], "AX24P02")
        self.assertEqual(parsed["observed_manufacturer"], "Apex Lifesciences Pvt Ltd")
        self.assertEqual(parsed["observed_expiry_date"], "2028-01-11")

    def test_authority_query_failure_means_unverified(self):
        records = {"manufacturer": [{}], "distributor": [{}], "retailer": [{}], "item_scan": [{}], "authority": []}
        statuses = {"manufacturer": "success", "distributor": "success", "retailer": "success", "item_scan": "success", "authority": "error"}
        result = integrate("MED1001", records, statuses)
        self.assertEqual(result["decision"], "UNVERIFIED")

    def test_missing_authority_row_means_unverified_not_asali(self):
        records = {
            "manufacturer": [{"ItemCode": "MED1001"}],
            "distributor": [{"ItemCode": "MED1001"}],
            "retailer": [{"ItemCode": "MED1001"}],
            "item_scan": [{"ItemCode": "MED1001"}],
            "authority": [],
        }
        statuses = {key: "success" for key in records}
        result = integrate("MED1001", records, statuses)
        self.assertEqual(result["decision"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
