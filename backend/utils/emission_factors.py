import json
import logging
from pathlib import Path
from typing import Any

import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_CONFIG: dict[str, Any] | None = None


def _get_config_path() -> Path:
    """Returns the path to the emission factors config file."""
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "config" / "emission_factors.json"


def load_config() -> dict[str, Any]:
    """Loads emission factors configuration from JSON file with environment variable overrides."""
    global _CONFIG
    
    if _CONFIG is not None:
        return _CONFIG
    
    config_path = _get_config_path()
    
    if not config_path.exists():
        logging.warning(f"Emission factors config not found at {config_path}. Using defaults.")
        return _get_default_config()
    
    try:
        with open(config_path, 'r') as f:
            _CONFIG = json.load(f)
        logging.info(f"Loaded emission factors from {config_path}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse emission factors config: {e}. Using defaults.")
        _CONFIG = _get_default_config()
    
    _apply_env_overrides()
    
    return _CONFIG


def _apply_env_overrides() -> None:
    """Allows environment variables to override config values."""
    global _CONFIG
    if _CONFIG is None:
        return
    
    if os.getenv("GRID_EMISSION_FACTOR"):
        try:
            factor = float(os.getenv("GRID_EMISSION_FACTOR"))
            _CONFIG["grid_emission_factors_kg_CO2_per_kWh"]["US_DEFAULT"] = factor
            logging.info(f"Overrode default grid factor via env: {factor}")
        except ValueError:
            logging.warning("Invalid GRID_EMISSION_FACTOR env value")
    
    if os.getenv("REGION_CODE"):
        region = os.getenv("REGION_CODE").upper()
        if region in _CONFIG["grid_emission_factors_kg_CO2_per_kWh"]:
            _CONFIG["grid_emission_factors_kg_CO2_per_kWh"]["US_DEFAULT"] = \
                _CONFIG["grid_emission_factors_kg_CO2_per_kWh"][region]
            logging.info(f"Set region to {region}")


def _get_default_config() -> dict[str, Any]:
    """Returns hardcoded defaults if config file is unavailable."""
    return {
        "grid_emission_factors_kg_CO2_per_kWh": {
            "US_DEFAULT": 0.386,
            "EU_DEFAULT": 0.276
        },
        "simulation_parameters": {
            "quarterly_variation_std": 0.10,
            "supplier_variation_std": 0.15,
            "dirichlet_alpha": 1.0,
            "min_quarterly_pct": 0.15,
            "max_quarterly_pct": 0.35
        },
        "deviation_thresholds": {
            "scope1_warning_pct": 5.0,
            "scope1_critical_pct": 15.0,
            "scope2_warning_pct": 5.0,
            "scope2_critical_pct": 15.0,
            "scope3_warning_pct": 10.0,
            "scope3_critical_pct": 25.0
        }
    }


def get_grid_factor(region_code: str | None = None) -> float:
    """
    Returns the grid emission factor for a given region.
    
    Args:
        region_code: Optional region code (e.g., 'US_CA', 'US_TX'). 
                     If None, uses the default.
    
    Returns:
        Emission factor in kg CO2 per kWh.
    """
    config = load_config()
    factors = config["grid_emission_factors_kg_CO2_per_kWh"]
    
    if region_code and region_code in factors:
        return factors[region_code]
    
    return factors.get("US_DEFAULT", 0.386)


def get_simulation_params() -> dict[str, Any]:
    """Returns simulation parameters from config."""
    config = load_config()
    return config.get("simulation_parameters", {
        "quarterly_variation_std": 0.10,
        "supplier_variation_std": 0.15,
        "dirichlet_alpha": 1.0,
        "min_quarterly_pct": 0.15,
        "max_quarterly_pct": 0.35
    })


def get_deviation_thresholds() -> dict[str, float]:
    """Returns deviation alert thresholds from config."""
    config = load_config()
    return config.get("deviation_thresholds", {
        "scope1_warning_pct": 5.0,
        "scope1_critical_pct": 15.0,
        "scope2_warning_pct": 5.0,
        "scope2_critical_pct": 15.0,
        "scope3_warning_pct": 10.0,
        "scope3_critical_pct": 25.0
    })


def reset_config() -> None:
    """Resets the cached config. Useful for testing."""
    global _CONFIG
    _CONFIG = None


if __name__ == "__main__":
    print("Grid emission factors:")
    print(load_config()["grid_emission_factors_kg_CO2_per_kWh"])
    print(f"\nDefault factor: {get_grid_factor()} kg CO2/kWh")
    print(f"California factor: {get_grid_factor('US_CA')} kg CO2/kWh")
    print(f"\nSimulation params: {get_simulation_params()}")
    print(f"\nDeviation thresholds: {get_deviation_thresholds()}")
