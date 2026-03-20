-- Migration: 001_add_enriched_columns.sql
-- Description: Adds columns for enriched emissions data including quarterly breakdowns,
--              supplier emissions, electricity estimates, and company metadata.
-- Author: Carbon-bot
-- Date: 2024-01-15

-- Add quarterly breakdown columns for each scope
ALTER TABLE company_emissions
ADD COLUMN IF NOT EXISTS scope1_q1 FLOAT,
ADD COLUMN IF NOT EXISTS scope1_q2 FLOAT,
ADD COLUMN IF NOT EXISTS scope1_q3 FLOAT,
ADD COLUMN IF NOT EXISTS scope1_q4 FLOAT,
ADD COLUMN IF NOT EXISTS scope2_q1 FLOAT,
ADD COLUMN IF NOT EXISTS scope2_q2 FLOAT,
ADD COLUMN IF NOT EXISTS scope2_q3 FLOAT,
ADD COLUMN IF NOT EXISTS scope2_q4 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_q1 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_q2 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_q3 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_q4 FLOAT;

-- Add supplier-level Scope 3 emissions (5 simulated suppliers)
ALTER TABLE company_emissions
ADD COLUMN IF NOT EXISTS scope3_supplier_1 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_supplier_2 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_supplier_3 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_supplier_4 FLOAT,
ADD COLUMN IF NOT EXISTS scope3_supplier_5 FLOAT;

-- Add methodology tracking
ALTER TABLE company_emissions
ADD COLUMN IF NOT EXISTS scope_distribution_method VARCHAR(50) DEFAULT 'normal_distribution',
ADD COLUMN IF NOT EXISTS scope3_supplier_method VARCHAR(50) DEFAULT 'dirichlet';

-- Add electricity consumption estimation
ALTER TABLE company_emissions
ADD COLUMN IF NOT EXISTS electricity_kwh FLOAT,
ADD COLUMN IF NOT EXISTS grid_emission_factor_used FLOAT;

-- Add company metadata
ALTER TABLE company_emissions
ADD COLUMN IF NOT EXISTS employee_count INTEGER,
ADD COLUMN IF NOT EXISTS energy_mix_renewable_pct FLOAT,
ADD COLUMN IF NOT EXISTS energy_mix_fossil_pct FLOAT,
ADD COLUMN IF NOT EXISTS energy_mix_nuclear_pct FLOAT,
ADD COLUMN IF NOT EXISTS energy_mix_other_pct FLOAT;

-- Add simulation flag
ALTER TABLE company_emissions
ADD COLUMN IF NOT EXISTS is_simulated BOOLEAN DEFAULT TRUE;

-- Add region code for emission factor lookup
ALTER TABLE company_emissions
ADD COLUMN IF NOT EXISTS region_code VARCHAR(20) DEFAULT 'US_DEFAULT';

-- Create index on company_name for faster lookups
CREATE INDEX IF NOT EXISTS idx_company_emissions_company_name ON company_emissions(company_name);

-- Create index on reporting_year for time-series analysis
CREATE INDEX IF NOT EXISTS idx_company_emissions_year ON company_emissions(reporting_year);

-- Create index on sector for sectoral analysis
CREATE INDEX IF NOT EXISTS idx_company_emissions_sector ON company_emissions(sector);

COMMENT ON TABLE company_emissions IS 'Enriched emissions data with quarterly breakdowns, supplier emissions, and company metadata';
COMMENT ON COLUMN company_emissions.electricity_kwh IS 'Estimated electricity consumption in kWh, back-calculated from Scope 2 emissions using grid emission factors';
COMMENT ON COLUMN company_emissions.scope_distribution_method IS 'Method used for quarterly distribution: normal_distribution or equal_split';
COMMENT ON COLUMN company_emissions.scope3_supplier_method IS 'Method used for supplier breakdown: dirichlet or uniform';
