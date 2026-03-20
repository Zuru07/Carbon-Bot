import logging
from typing import TypedDict

import numpy as np
import pandas as pd

from .emission_factors import get_grid_factor, get_simulation_params

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class QuarterlyBreakdown(TypedDict):
    q1: float
    q2: float
    q3: float
    q4: float


class SupplierBreakdown(TypedDict):
    supplier_id: str
    supplier_name: str
    emissions_tCO2e: float
    proportion: float


class ElectricityEstimation(TypedDict):
    scope2_tCO2e: float
    grid_factor_kg_per_kwh: float
    electricity_kwh: float
    region_code: str


class Metadata(TypedDict):
    employee_count: int
    energy_mix_renewable_pct: float
    energy_mix_fossil_pct: float
    energy_mix_nuclear_pct: float
    energy_mix_other_pct: float


def generate_quarterly_breakdown(
    annual_total: float,
    variation_std: float | None = None,
    min_pct: float | None = None,
    max_pct: float | None = None
) -> QuarterlyBreakdown:
    """
    Splits annual emissions into quarterly values using a normal distribution.
    
    Uses controlled variation to simulate realistic seasonal fluctuations
    while ensuring the sum of all quarters equals the annual total.
    
    Args:
        annual_total: Total annual emissions in tCO2e
        variation_std: Standard deviation for normal distribution (0.0-1.0)
        min_pct: Minimum allowed percentage for any quarter
        max_pct: Maximum allowed percentage for any quarter
    
    Returns:
        Dictionary with q1, q2, q3, q4 values
    """
    if variation_std is None:
        variation_std = get_simulation_params()["quarterly_variation_std"]
    if min_pct is None:
        min_pct = get_simulation_params()["min_quarterly_pct"]
    if max_pct is None:
        max_pct = get_simulation_params()["max_quarterly_pct"]
    
    if annual_total <= 0:
        return {"q1": 0.0, "q2": 0.0, "q3": 0.0, "q4": 0.0}
    
    base_share = 0.25
    variations = np.random.normal(0, variation_std, 4)
    
    shares = np.array([base_share, base_share, base_share, base_share]) + variations
    shares = np.clip(shares, min_pct, max_pct)
    
    shares = shares / shares.sum()
    
    quarterly_values = shares * annual_total
    
    return {
        "q1": float(quarterly_values[0]),
        "q2": float(quarterly_values[1]),
        "q3": float(quarterly_values[2]),
        "q4": float(quarterly_values[3])
    }


def estimate_electricity_consumption(
    scope2_tCO2e: float,
    grid_factor: float | None = None,
    region_code: str = "US_DEFAULT"
) -> ElectricityEstimation:
    """
    Back-calculates electricity consumption from Scope 2 emissions.
    
    Uses the formula: electricity_kWh = Scope2_tCO2e / grid_factor_kg_per_kWh
    Converts from metric tons to kg first.
    
    Args:
        scope2_tCO2e: Scope 2 emissions in metric tons CO2e
        grid_factor: Emission factor in kg CO2 per kWh
        region_code: Region code for looking up grid factor if not provided
    
    Returns:
        Dictionary with electricity estimation details
    """
    if grid_factor is None:
        grid_factor = get_grid_factor(region_code)
    
    if scope2_tCO2e <= 0 or grid_factor <= 0:
        return {
            "scope2_tCO2e": float(scope2_tCO2e),
            "grid_factor_kg_per_kwh": float(grid_factor),
            "electricity_kwh": 0.0,
            "region_code": region_code
        }
    
    scope2_kg = scope2_tCO2e * 1000
    
    electricity_kwh = scope2_kg / grid_factor
    
    return {
        "scope2_tCO2e": float(scope2_tCO2e),
        "grid_factor_kg_per_kwh": float(grid_factor),
        "electricity_kwh": float(electricity_kwh),
        "region_code": region_code
    }


def generate_supplier_breakdown(
    scope3_total: float,
    n_suppliers: int = 5,
    method: str = "dirichlet",
    alpha: float | None = None
) -> list[SupplierBreakdown]:
    """
    Breaks down Scope 3 emissions into supplier-specific values.
    
    Uses Dirichlet distribution for proportional contributions that
    sum to the total, simulating realistic supplier variations.
    
    Args:
        scope3_total: Total Scope 3 emissions in tCO2e
        n_suppliers: Number of suppliers to simulate
        method: Distribution method ('dirichlet' or 'uniform')
        alpha: Dirichlet concentration parameter (higher = more equal)
    
    Returns:
        List of dictionaries with supplier breakdown data
    """
    if scope3_total <= 0:
        return []
    
    if alpha is None:
        alpha = get_simulation_params()["dirichlet_alpha"]
    
    if method == "dirichlet":
        alphas = np.ones(n_suppliers) * alpha
        proportions = np.random.dirichlet(alphas)
    else:
        proportions = np.ones(n_suppliers) / n_suppliers
    
    suppliers = []
    for i, prop in enumerate(proportions):
        supplier_id = f"SUP_{i+1:03d}"
        supplier_name = f"Supplier_{chr(65+i)}"
        emissions = prop * scope3_total
        
        suppliers.append({
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "emissions_tCO2e": float(emissions),
            "proportion": float(prop)
        })
    
    return suppliers


def generate_metadata(
    scope1: float,
    scope2: float,
    scope3: float,
    sector: str | None = None
) -> Metadata:
    """
    Generates simulated metadata for a company including employee count
    and energy mix percentages.
    
    Uses company size proxies based on emissions and sector-based
    energy mix assumptions.
    
    Args:
        scope1: Scope 1 emissions in tCO2e
        scope2: Scope 2 emissions in tCO2e
        scope3: Scope 3 emissions in tCO2e
        sector: Company sector for energy mix estimation
    
    Returns:
        Dictionary with metadata fields
    """
    total_emissions = scope1 + scope2 + scope3
    
    base_employees = 1000
    if total_emissions > 10000000:
        base_employees = 50000
    elif total_emissions > 1000000:
        base_employees = 15000
    elif total_emissions > 100000:
        base_employees = 5000
    elif total_emissions > 10000:
        base_employees = 2000
    
    employee_variation = np.random.uniform(0.7, 1.3)
    employee_count = int(base_employees * employee_variation)
    
    if sector and sector.lower() in ["technology", "financial", "services"]:
        renewable_pct = np.random.uniform(60, 90)
        fossil_pct = np.random.uniform(5, 20)
        nuclear_pct = np.random.uniform(5, 20)
    elif sector and sector.lower() in ["manufacturing", "industrial", "energy"]:
        renewable_pct = np.random.uniform(15, 35)
        fossil_pct = np.random.uniform(40, 65)
        nuclear_pct = np.random.uniform(10, 25)
    else:
        renewable_pct = np.random.uniform(25, 50)
        fossil_pct = np.random.uniform(30, 50)
        nuclear_pct = np.random.uniform(10, 30)
    
    total_energy = renewable_pct + fossil_pct + nuclear_pct
    other_pct = max(0, 100 - total_energy)
    
    remaining = 100 - other_pct
    scale = 100 / (renewable_pct + fossil_pct + nuclear_pct)
    renewable_pct *= scale
    fossil_pct *= scale
    nuclear_pct *= scale
    
    return {
        "employee_count": employee_count,
        "energy_mix_renewable_pct": float(renewable_pct),
        "energy_mix_fossil_pct": float(fossil_pct),
        "energy_mix_nuclear_pct": float(nuclear_pct),
        "energy_mix_other_pct": float(other_pct)
    }


def enrich_dataframe_with_simulations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies all simulation functions to a DataFrame of company emissions data.
    
    Adds quarterly breakdowns, electricity estimations, supplier breakdowns
    (stored as JSON strings), and metadata columns.
    
    Args:
        df: DataFrame with company_name, sector, scope1_total, scope2_total, scope3_total
    
    Returns:
        DataFrame with added simulation columns
    """
    logging.info(f"Starting data enrichment for {len(df)} companies...")
    
    result_df = df.copy()
    
    for scope in ["scope1", "scope2", "scope3"]:
        total_col = f"{scope}_total"
        if total_col not in result_df.columns:
            continue
        
        logging.info(f"Generating quarterly breakdown for {scope}...")
        
        q_cols = {}
        for q in ["q1", "q2", "q3", "q4"]:
            q_cols[f"{scope}_{q}"] = []
        
        for _, row in result_df.iterrows():
            quarterly = generate_quarterly_breakdown(row[total_col])
            for q, value in quarterly.items():
                q_cols[f"{scope}_{q}"].append(value)
        
        for col_name, values in q_cols.items():
            result_df[col_name] = values
    
    logging.info("Estimating electricity consumption...")
    electricity_kwh_values = []
    grid_factors_used = []
    for _, row in result_df.iterrows():
        scope2 = row.get("scope2_total", 0)
        region = row.get("region_code", "US_DEFAULT")
        estimation = estimate_electricity_consumption(scope2, region_code=region)
        electricity_kwh_values.append(estimation["electricity_kwh"])
        grid_factors_used.append(estimation["grid_factor_kg_per_kwh"])
    
    result_df["electricity_kwh"] = electricity_kwh_values
    result_df["grid_emission_factor_used"] = grid_factors_used
    
    n_suppliers = 5
    supplier_data = {}
    for i in range(1, n_suppliers + 1):
        supplier_data[f"scope3_supplier_{i}"] = []
    
    for _, row in result_df.iterrows():
        scope3 = row.get("scope3_total", 0)
        suppliers = generate_supplier_breakdown(scope3, n_suppliers=n_suppliers)
        for i in range(n_suppliers):
            if i < len(suppliers):
                supplier_data[f"scope3_supplier_{i+1}"].append(suppliers[i]["emissions_tCO2e"])
            else:
                supplier_data[f"scope3_supplier_{i+1}"].append(0.0)
    
    for col_name, values in supplier_data.items():
        result_df[col_name] = values
    
    result_df["scope3_supplier_method"] = "dirichlet"
    result_df["scope_distribution_method"] = "normal_distribution"
    
    logging.info("Generating metadata...")
    metadata_cols = ["employee_count", "energy_mix_renewable_pct", 
                     "energy_mix_fossil_pct", "energy_mix_nuclear_pct",
                     "energy_mix_other_pct"]
    for col in metadata_cols:
        result_df[col] = 0.0
    
    for idx, row in result_df.iterrows():
        metadata = generate_metadata(
            row.get("scope1_total", 0),
            row.get("scope2_total", 0),
            row.get("scope3_total", 0),
            row.get("sector", None)
        )
        for key, value in metadata.items():
            result_df.at[idx, key] = value
    
    result_df["is_simulated"] = True
    
    logging.info(f"Data enrichment complete. Added columns: {list(result_df.columns)}")
    return result_df


if __name__ == "__main__":
    np.random.seed(42)
    
    print("=== Testing Emission Calculator ===\n")
    
    annual = 100000.0
    print(f"Annual emissions: {annual} tCO2e")
    quarterly = generate_quarterly_breakdown(annual)
    print(f"Quarterly breakdown: {quarterly}")
    print(f"Sum check: {sum(quarterly.values())} (should be ~{annual})\n")
    
    scope2 = 50000.0
    elec = estimate_electricity_consumption(scope2, region_code="US_CA")
    print(f"Electricity estimation from {scope2} tCO2e Scope 2:")
    print(f"  Grid factor: {elec['grid_factor_kg_per_kwh']} kg/kWh")
    print(f"  Estimated electricity: {elec['electricity_kwh']:,.0f} kWh\n")
    
    scope3 = 500000.0
    suppliers = generate_supplier_breakdown(scope3, n_suppliers=5)
    print(f"Supplier breakdown for {scope3} tCO2e Scope 3:")
    for s in suppliers:
        print(f"  {s['supplier_name']}: {s['emissions_tCO2e']:,.0f} tCO2e ({s['proportion']:.1%})")
    print(f"  Sum check: {sum(s['emissions_tCO2e'] for s in suppliers):,.0f}\n")
    
    metadata = generate_metadata(100000, 50000, 500000, sector="Technology")
    print(f"Generated metadata: {metadata}\n")
    
    print("=== Testing DataFrame Enrichment ===")
    test_df = pd.DataFrame({
        "company_name": ["Company A", "Company B"],
        "sector": ["Technology", "Manufacturing"],
        "scope1_total": [100000, 200000],
        "scope2_total": [50000, 80000],
        "scope3_total": [500000, 1000000],
        "region_code": ["US_CA", "US_TX"]
    })
    enriched = enrich_dataframe_with_simulations(test_df)
    print(f"Original columns: {len(test_df.columns)}")
    print(f"Enriched columns: {len(enriched.columns)}")
    print(f"New columns: {[c for c in enriched.columns if c not in test_df.columns]}")
