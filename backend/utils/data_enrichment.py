import logging
from typing import Literal

import pandas as pd

from .emission_calculator import enrich_dataframe_with_simulations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def enrich_emissions_data(
    df: pd.DataFrame,
    num_simulated_suppliers: int = 5,
    method: Literal["distribution", "equal_split"] = "distribution"
) -> pd.DataFrame:
    """
    Enriches the emissions DataFrame with simulated quarterly breakdowns,
    supplier-level Scope 3 data, electricity consumption estimates, and metadata.
    
    Args:
        df: Input DataFrame with company emissions data
        num_simulated_suppliers: Number of suppliers to simulate (default: 5)
        method: Simulation method - 'distribution' uses normal/Dirichlet 
                distributions, 'equal_split' uses simple division
    
    Returns:
        Enriched DataFrame with additional simulation columns
    """
    logging.info(f"Starting data enrichment (method: {method})...")
    
    if method == "distribution":
        return enrich_dataframe_with_simulations(df)
    
    enriched_df = df.copy()
    
    for scope in ["scope1", "scope2", "scope3"]:
        total_col = f"{scope}_total"
        if total_col not in enriched_df.columns:
            continue
        for i in range(1, 5):
            enriched_df[f"{scope}_q{i}"] = enriched_df[total_col] / 4.0
            
    enriched_df["scope_distribution_method"] = "equal_split"

    logging.info(f"Simulating Scope 3 breakdown for {num_simulated_suppliers} suppliers.")
    scope3_per_supplier = enriched_df["scope3_total"] / num_simulated_suppliers
    for i in range(1, num_simulated_suppliers + 1):
        enriched_df[f"scope3_supplier_{i}"] = scope3_per_supplier
        
    enriched_df["scope3_supplier_method"] = "equal_split_simulated"

    enriched_df["is_simulated"] = True
    
    logging.info("Data enrichment complete (legacy equal-split method).")
    return enriched_df


def get_enrichment_summary(df: pd.DataFrame) -> dict:
    """
    Returns a summary of the enrichment applied to the DataFrame.
    
    Args:
        df: Enriched DataFrame
    
    Returns:
        Dictionary with enrichment statistics
    """
    summary = {
        "total_companies": len(df),
        "has_quarterly_data": any("q1" in col for col in df.columns),
        "has_supplier_data": any("supplier" in col.lower() for col in df.columns),
        "has_electricity_data": "electricity_kwh" in df.columns,
        "has_metadata": "employee_count" in df.columns,
        "simulation_method": df.iloc[0]["scope_distribution_method"] if len(df) > 0 and "scope_distribution_method" in df.columns else "unknown",
        "supplier_count": sum(1 for col in df.columns if "scope3_supplier_" in col),
        "total_electricity_kwh": float(df["electricity_kwh"].sum()) if "electricity_kwh" in df.columns else 0,
        "total_employees": int(df["employee_count"].sum()) if "employee_count" in df.columns else 0
    }
    
    return summary


if __name__ == "__main__":
    import numpy as np
    
    np.random.seed(42)
    
    print("=== Testing Data Enrichment ===\n")
    
    test_df = pd.DataFrame({
        "company_name": ["Company A", "Company B", "Company C"],
        "sector": ["Technology", "Manufacturing", "Energy"],
        "scope1_total": [100000.0, 200000.0, 500000.0],
        "scope2_total": [50000.0, 80000.0, 200000.0],
        "scope3_total": [500000.0, 1000000.0, 2000000.0],
        "region_code": ["US_CA", "US_TX", "US_NY"]
    })
    
    print("Original DataFrame:")
    print(test_df.head())
    print(f"\nColumns: {list(test_df.columns)}\n")
    
    enriched_df = enrich_emissions_data(test_df, method="distribution")
    
    print("\nEnriched DataFrame:")
    print(enriched_df.head())
    print(f"\nNew columns: {[c for c in enriched_df.columns if c not in test_df.columns]}")
    
    summary = get_enrichment_summary(enriched_df)
    print("\nEnrichment Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
