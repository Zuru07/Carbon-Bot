-- Migration: 002_add_alerts_and_history.sql
-- Creates tables for deviation alerts and historical emissions tracking

CREATE TABLE IF NOT EXISTS deviation_alerts (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    reporting_year INTEGER NOT NULL,
    metric VARCHAR(50) NOT NULL,
    previous_value FLOAT,
    current_value FLOAT,
    change_pct FLOAT NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(255),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_deviation_alerts_company ON deviation_alerts(company_name);
CREATE INDEX IF NOT EXISTS idx_deviation_alerts_severity ON deviation_alerts(severity);

CREATE TABLE IF NOT EXISTS emissions_history (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    reporting_year INTEGER NOT NULL,
    scope1_total FLOAT NOT NULL,
    scope2_total FLOAT NOT NULL,
    scope3_total FLOAT NOT NULL,
    electricity_kwh FLOAT,
    employee_count INTEGER,
    energy_mix_renewable_pct FLOAT,
    energy_mix_fossil_pct FLOAT,
    energy_mix_nuclear_pct FLOAT,
    snapshot_date DATE DEFAULT CURRENT_DATE,
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(500),
    is_simulated BOOLEAN DEFAULT FALSE,
    UNIQUE(company_name, reporting_year, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_emissions_history_company ON emissions_history(company_name);
CREATE INDEX IF NOT EXISTS idx_emissions_history_year ON emissions_history(reporting_year);
