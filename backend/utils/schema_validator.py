import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_emissions_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates the schema of the emissions DataFrame, checks for required columns,
    ensures correct data types, and logs warnings for missing optional columns.
    """
    logging.info("Starting schema validation...")
    
    required_columns = {
        "company_name": str,
        "sector": str,
        "reporting_year": int,
        "scope1_total": float,
        "scope2_total": float,
        "scope3_total": float
    }
    
    optional_columns = ["supplier_id", "country", "region", "headquarters_country"]
    
    missing_required = set(required_columns.keys()) - set(df.columns)
    if missing_required:
        raise ValueError(f"Missing required columns in the input data: {list(missing_required)}")

    missing_optional = set(optional_columns) - set(df.columns)
    if missing_optional:
        logging.warning(f"Missing optional columns: {list(missing_optional)}. Pipeline will continue.")

    validated_df = df.copy()
    for col, col_type in required_columns.items():
        try:
            if validated_df[col].isnull().any() and col_type == int:
                raise ValueError(f"Column '{col}' contains null values and cannot be cast to integer.")
            validated_df[col] = validated_df[col].astype(col_type)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Could not convert column '{col}' to type {col_type}. Reason: {e}")

    logging.info("Schema validation successful.")
    return validated_df