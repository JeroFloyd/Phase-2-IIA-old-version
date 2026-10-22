USE authority_db;

DROP TABLE IF EXISTS consumer_report;

CREATE TABLE consumer_report (
    ReportId INT PRIMARY KEY,
    ReportedCode VARCHAR(20) NOT NULL,
    ComplaintType VARCHAR(80) NOT NULL,
    ReportDate DATE NOT NULL,
    MinistryStatus ENUM('NO_ADVERSE_REPORT','UNDER_REVIEW','CONFIRMED_NAKALI') NOT NULL,
    CaseReference VARCHAR(40) NOT NULL UNIQUE,
    EvidenceNote VARCHAR(255)
);
CREATE INDEX idx_reported_code ON consumer_report(ReportedCode);
