import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def enrich_emissions_data(df: pd.DataFrame, num_simulated_suppliers: int = 5) -> pd.DataFrame:
    """
    Enriches the emissions DataFrame with simulated quarterly breakdowns and
    supplier-level Scope 3 data.
    """
    logging.info("Starting data enrichment...")
    
    enriched_df = df.copy()
    
    # --- Quarterly Breakdowns ---
    for scope in ["scope1", "scope2", "scope3"]:
        total_col = f"{scope}_total"
        for i in range(1, 5):
            enriched_df[f"{scope}_q{i}"] = enriched_df[total_col] / 4.0
            
    enriched_df["scope_distribution_method"] = "equal_split"

    # --- Supplier-level Scope 3 ---
    logging.info(f"Simulating Scope 3 breakdown for {num_simulated_suppliers} suppliers.")
    scope3_per_supplier = enriched_df["scope3_total"] / num_simulated_suppliers
    for i in range(1, num_simulated_suppliers + 1):
        enriched_df[f"scope3_supplier_{i}"] = scope3_per_supplier
        
    enriched_df["scope3_supplier_method"] = "equal_split_simulated"

    # --- Traceability ---
    enriched_df["is_simulated"] = True
    
    logging.info("Data enrichment complete.")
    return enriched_df