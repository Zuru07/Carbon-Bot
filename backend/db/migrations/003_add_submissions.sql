-- Migration: 003_add_submissions.sql
-- Creates table for tracking ESG report submissions

CREATE TABLE IF NOT EXISTS submission_history (
    id SERIAL PRIMARY KEY,
    confirmation_id UUID NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    reporting_year INTEGER,
    report_version INTEGER DEFAULT 1,
    file_location VARCHAR(500) NOT NULL,
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submission_status VARCHAR(50) NOT NULL,
    validated_successfully BOOLEAN DEFAULT TRUE,
    validation_errors TEXT,
    report_type VARCHAR(50),
    total_emissions_tCO2e FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_submission_history_company ON submission_history(company_name);
CREATE INDEX IF NOT EXISTS idx_submission_history_year ON submission_history(reporting_year);
CREATE INDEX IF NOT EXISTS idx_submission_history_confirmation ON submission_history(confirmation_id);

CREATE OR REPLACE VIEW recent_submissions AS
SELECT 
    confirmation_id,
    company_name,
    reporting_year,
    report_version,
    submission_status,
    submitted_at
FROM submission_history
ORDER BY submitted_at DESC
LIMIT 100;
