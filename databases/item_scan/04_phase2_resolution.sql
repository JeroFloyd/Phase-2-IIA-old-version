-- Phase 2 migration: additive only; does not drop or change the Part A tables/views.
-- Run on the teammate's MySQL Server as an administrative account.
USE item_scan_db;

CREATE TABLE IF NOT EXISTS phase2_observation_resolution (
    ResolutionId BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    RawImageName VARCHAR(255) NULL,
    RawOCRText TEXT NOT NULL,
    ObservedItemCode VARCHAR(40) NOT NULL,
    ObservedProductName VARCHAR(150) NULL,
    ObservedBatchNo VARCHAR(50) NULL,
    ObservedManufacturer VARCHAR(150) NULL,
    ObservedExpiryDate VARCHAR(30) NULL,
    CanonicalItemCode VARCHAR(20) NULL,
    MatchScore DECIMAL(5,2) NULL,
    MatchStatus VARCHAR(32) NOT NULL,
    MatchReason TEXT NOT NULL,
    IsHumanApproved BOOLEAN NOT NULL DEFAULT FALSE,
    CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_p2_observed_code (ObservedItemCode),
    INDEX idx_p2_canonical_code (CanonicalItemCode),
    INDEX idx_p2_match_status (MatchStatus),
    INDEX idx_p2_created_at (CreatedAt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SHOW TABLES LIKE 'phase2_observation_resolution';
