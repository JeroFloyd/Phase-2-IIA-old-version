USE authority_db;
CREATE OR REPLACE VIEW authority_item_view AS
SELECT ReportedCode AS ItemCode,
       ComplaintType,
       ReportDate,
       MinistryStatus,
       CaseReference,
       EvidenceNote
FROM consumer_report;
