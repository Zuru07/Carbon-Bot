import logging
from datetime import datetime
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from backend.utils.emission_factors import get_grid_factor, get_deviation_thresholds

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SustainabilityAgent:
    """
    An agent for performing structured analytical queries against the
    PostgreSQL database with support for emissions analysis, energy
    consumption estimation, deviation detection, and historical tracking.
    """

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        load_dotenv(dotenv_path=self.project_root / ".env")
        
        self.db_uri = os.getenv("POSTGRES_URI")
        self.table_name = os.getenv("POSTGRES_TABLE_NAME", "company_emissions")
        if not self.db_uri:
            raise ValueError("POSTGRES_URI environment variable is not set.")
        
        self.engine = create_engine(
            self.db_uri,
            pool_recycle=1800,
            connect_args={'connect_timeout': 10}
        )
        logging.info("SustainabilityAgent initialized.")

    def get_company_snapshot(self, company_name: str) -> dict | None:
        """
        Retrieves all data for a single company including enriched fields.
        
        Args:
            company_name: Name of the company to retrieve
            
        Returns:
            Dictionary with all company data or None if not found
        """
        logging.info(f"Fetching snapshot for company: '{company_name}'")
        try:
            with self.engine.connect() as connection:
                query = text(f"SELECT * FROM {self.table_name} WHERE company_name = :c_name")
                df = pd.read_sql(query, connection, params={"c_name": company_name})
            
            if df.empty:
                logging.warning(f"No data found for company: '{company_name}'")
                return None
            
            result_dict = df.to_dict('records')[0]
            for key, value in result_dict.items():
                if pd.isna(value):
                    result_dict[key] = None
                elif hasattr(value, 'item'):
                    result_dict[key] = value.item()
            return result_dict

        except Exception as e:
            logging.error(f"Error fetching company snapshot for '{company_name}': {e}", exc_info=True)
            return None

    def get_all_company_names(self) -> list:
        """Retrieves a list of all unique company names."""
        logging.info("Fetching all company names.")
        try:
            with self.engine.connect() as connection:
                query = f"SELECT DISTINCT company_name FROM {self.table_name} ORDER BY company_name;"
                df = pd.read_sql(query, connection)
            return df['company_name'].tolist()
        except Exception as e:
            logging.error(f"Error fetching company names: {e}", exc_info=True)
            return []

    def get_energy_consumption(
        self,
        company_name: str,
        region_code: str | None = None
    ) -> dict | None:
        """
        Calculates estimated electricity consumption from Scope 2 emissions.
        
        Args:
            company_name: Name of the company
            region_code: Optional region code to override stored value
            
        Returns:
            Dictionary with electricity estimation details or None if company not found
        """
        snapshot = self.get_company_snapshot(company_name)
        if not snapshot:
            return None
        
        scope2_tCO2e = snapshot.get('scope2_total', 0)
        if scope2_tCO2e is None or scope2_tCO2e <= 0:
            return {
                "company_name": company_name,
                "scope2_tCO2e": 0,
                "electricity_kwh": 0,
                "grid_factor_kg_per_kwh": 0,
                "region_code": region_code or snapshot.get('region_code', 'US_DEFAULT')
            }
        
        if region_code is None:
            region_code = snapshot.get('region_code', 'US_DEFAULT')
        
        grid_factor = get_grid_factor(region_code)
        scope2_kg = scope2_tCO2e * 1000
        electricity_kwh = scope2_kg / grid_factor
        
        return {
            "company_name": company_name,
            "scope2_tCO2e": float(scope2_tCO2e),
            "electricity_kwh": float(electricity_kwh),
            "grid_factor_kg_per_kwh": float(grid_factor),
            "region_code": region_code,
            "reporting_year": snapshot.get('reporting_year')
        }

    def check_deviation_alerts(
        self,
        company_name: str,
        threshold_pct: float = 10.0
    ) -> list[dict]:
        """
        Checks for significant year-over-year changes in emissions data.
        
        Compares current year emissions with previous year and flags deviations
        exceeding the threshold percentage.
        
        Args:
            company_name: Name of the company to check
            threshold_pct: Percentage change to trigger an alert (default: 10%)
            
        Returns:
            List of alert dictionaries for any detected deviations
        """
        logging.info(f"Checking deviation alerts for '{company_name}' (threshold: {threshold_pct}%)")
        
        thresholds = get_deviation_thresholds()
        
        try:
            with self.engine.connect() as connection:
                query = text(f"""
                    SELECT company_name, reporting_year, 
                           scope1_total, scope2_total, scope3_total
                    FROM {self.table_name}
                    WHERE company_name = :c_name
                    ORDER BY reporting_year DESC
                    LIMIT 2
                """)
                df = pd.read_sql(query, connection, params={"c_name": company_name})
            
            if len(df) < 2:
                logging.info(f"Insufficient data for deviation check on '{company_name}' (need 2+ years)")
                return []
            
            current = df.iloc[0]
            previous = df.iloc[1]
            
            alerts = []
            metrics = [
                ('scope1', 'scope1_total', thresholds['scope1_warning_pct'], thresholds['scope1_critical_pct']),
                ('scope2', 'scope2_total', thresholds['scope2_warning_pct'], thresholds['scope2_critical_pct']),
                ('scope3', 'scope3_total', thresholds['scope3_warning_pct'], thresholds['scope3_critical_pct']),
            ]
            
            for metric_name, col_name, warning_thresh, critical_thresh in metrics:
                prev_val = previous[col_name] or 0
                curr_val = current[col_name] or 0
                
                if prev_val == 0:
                    if curr_val > 0:
                        alerts.append({
                            "company_name": company_name,
                            "reporting_year": int(current['reporting_year']),
                            "metric": metric_name,
                            "previous_value": prev_val,
                            "current_value": curr_val,
                            "change_pct": 100.0,
                            "severity": "warning",
                            "message": f"{metric_name.upper()} is new data (was 0)"
                        })
                    continue
                
                change_pct = ((curr_val - prev_val) / prev_val) * 100
                abs_change_pct = abs(change_pct)
                
                if abs_change_pct >= critical_thresh:
                    severity = "critical"
                elif abs_change_pct >= warning_thresh:
                    severity = "warning"
                else:
                    continue
                
                alert = {
                    "company_name": company_name,
                    "reporting_year": int(current['reporting_year']),
                    "metric": metric_name,
                    "previous_value": float(prev_val),
                    "current_value": float(curr_val),
                    "change_pct": float(change_pct),
                    "severity": severity,
                    "message": f"{metric_name.upper()} changed by {change_pct:.1f}%"
                }
                alerts.append(alert)
                
                self._store_alert(alert)
            
            return alerts
            
        except Exception as e:
            logging.error(f"Error checking deviation alerts for '{company_name}': {e}", exc_info=True)
            return []

    def _store_alert(self, alert: dict) -> bool:
        """Stores an alert in the deviation_alerts table."""
        try:
            with self.engine.connect() as connection:
                insert_query = text("""
                    INSERT INTO deviation_alerts 
                    (company_name, reporting_year, metric, previous_value, current_value, change_pct, severity)
                    VALUES (:company_name, :reporting_year, :metric, :previous_value, :current_value, :change_pct, :severity)
                """)
                connection.execute(insert_query, {
                    "company_name": alert["company_name"],
                    "reporting_year": alert["reporting_year"],
                    "metric": alert["metric"],
                    "previous_value": alert["previous_value"],
                    "current_value": alert["current_value"],
                    "change_pct": alert["change_pct"],
                    "severity": alert["severity"]
                })
                connection.commit()
            logging.info(f"Stored alert: {alert['company_name']} - {alert['metric']} ({alert['severity']})")
            return True
        except SQLAlchemyError as e:
            logging.warning(f"Could not store alert (table may not exist): {e}")
            return False

    def get_alerts(
        self,
        company_name: str | None = None,
        severity: str | None = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Retrieves deviation alerts, optionally filtered.
        
        Args:
            company_name: Filter by company name
            severity: Filter by severity ('info', 'warning', 'critical')
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert dictionaries
        """
        try:
            with self.engine.connect() as connection:
                conditions = []
                params = {"limit": limit}
                
                if company_name:
                    conditions.append("company_name = :company_name")
                    params["company_name"] = company_name
                
                if severity:
                    conditions.append("severity = :severity")
                    params["severity"] = severity
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                query = text(f"""
                    SELECT * FROM deviation_alerts
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit
                """)
                df = pd.read_sql(query, connection, params=params)
            
            return df.to_dict('records')
        except SQLAlchemyError as e:
            logging.warning(f"Could not retrieve alerts (table may not exist): {e}")
            return []

    def get_historical_trends(
        self,
        company_name: str,
        years: int = 5
    ) -> list[dict]:
        """
        Retrieves historical emissions data for trend analysis.
        
        Args:
            company_name: Name of the company
            years: Number of years of history to retrieve
            
        Returns:
            List of yearly emissions records sorted by year
        """
        logging.info(f"Fetching historical trends for '{company_name}' (up to {years} years)")
        
        try:
            with self.engine.connect() as connection:
                query = text(f"""
                    SELECT company_name, reporting_year,
                           scope1_total, scope2_total, scope3_total,
                           scope1_total + scope2_total + scope3_total AS total_emissions,
                           electricity_kwh, employee_count
                    FROM {self.table_name}
                    WHERE company_name = :c_name
                    ORDER BY reporting_year DESC
                    LIMIT :years
                """)
                df = pd.read_sql(query, connection, params={"c_name": company_name, "years": years})
            
            if df.empty:
                return []
            
            records = df.to_dict('records')
            for record in records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
            
            return records
            
        except Exception as e:
            logging.error(f"Error fetching historical trends for '{company_name}': {e}", exc_info=True)
            return []

    def get_emissions_summary(self, company_name: str) -> dict | None:
        """
        Gets a formatted emissions summary for a company.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Dictionary with formatted emissions summary
        """
        snapshot = self.get_company_snapshot(company_name)
        if not snapshot:
            return None
        
        summary = {
            "company_name": company_name,
            "reporting_year": snapshot.get('reporting_year'),
            "sector": snapshot.get('sector'),
            "emissions": {
                "scope1_tCO2e": snapshot.get('scope1_total'),
                "scope2_tCO2e": snapshot.get('scope2_total'),
                "scope3_tCO2e": snapshot.get('scope3_total'),
                "total_tCO2e": (
                    (snapshot.get('scope1_total') or 0) +
                    (snapshot.get('scope2_total') or 0) +
                    (snapshot.get('scope3_total') or 0)
                )
            },
            "quarterly": {
                "scope1": {
                    "q1": snapshot.get('scope1_q1'),
                    "q2": snapshot.get('scope1_q2'),
                    "q3": snapshot.get('scope1_q3'),
                    "q4": snapshot.get('scope1_q4')
                },
                "scope2": {
                    "q1": snapshot.get('scope2_q1'),
                    "q2": snapshot.get('scope2_q2'),
                    "q3": snapshot.get('scope2_q3'),
                    "q4": snapshot.get('scope2_q4')
                },
                "scope3": {
                    "q1": snapshot.get('scope3_q1'),
                    "q2": snapshot.get('scope3_q2'),
                    "q3": snapshot.get('scope3_q3'),
                    "q4": snapshot.get('scope3_q4')
                }
            },
            "energy": {
                "electricity_kwh": snapshot.get('electricity_kwh'),
                "grid_emission_factor": snapshot.get('grid_emission_factor_used')
            },
            "metadata": {
                "employee_count": snapshot.get('employee_count'),
                "energy_mix": {
                    "renewable_pct": snapshot.get('energy_mix_renewable_pct'),
                    "fossil_pct": snapshot.get('energy_mix_fossil_pct'),
                    "nuclear_pct": snapshot.get('energy_mix_nuclear_pct'),
                    "other_pct": snapshot.get('energy_mix_other_pct')
                }
            }
        }
        
        return summary


import os

if __name__ == '__main__':
    try:
        agent = SustainabilityAgent()
        
        print("\n=== Testing Sustainability Agent ===\n")
        
        names = agent.get_all_company_names()
        print(f"Found {len(names)} companies.")
        
        if names:
            test_company = names[0]
            print(f"\n--- Testing company: {test_company} ---\n")
            
            snapshot = agent.get_company_snapshot(test_company)
            if snapshot:
                print(f"Company: {snapshot.get('company_name')}")
                print(f"Total Emissions: {snapshot.get('scope1_total', 0) + snapshot.get('scope2_total', 0) + snapshot.get('scope3_total', 0):,.0f} tCO2e")
            
            energy = agent.get_energy_consumption(test_company)
            if energy:
                print(f"\nElectricity Estimation:")
                print(f"  Scope 2: {energy['scope2_tCO2e']:,.0f} tCO2e")
                print(f"  Grid Factor: {energy['grid_factor_kg_per_kwh']} kg CO2/kWh")
                print(f"  Estimated Electricity: {energy['electricity_kwh']:,.0f} kWh")
            
            summary = agent.get_emissions_summary(test_company)
            if summary:
                print(f"\nEmissions Summary:")
                print(f"  Scope 1: {summary['emissions']['scope1_tCO2e']:,.0f} tCO2e")
                print(f"  Scope 2: {summary['emissions']['scope2_tCO2e']:,.0f} tCO2e")
                print(f"  Scope 3: {summary['emissions']['scope3_tCO2e']:,.0f} tCO2e")
            
            alerts = agent.check_deviation_alerts(test_company)
            print(f"\nDeviation Alerts: {len(alerts)} found")
            for alert in alerts:
                print(f"  [{alert['severity'].upper()}] {alert['metric']}: {alert['message']}")
            
            trends = agent.get_historical_trends(test_company, years=3)
            print(f"\nHistorical Trends: {len(trends)} records")
            for trend in trends:
                print(f"  {trend['reporting_year']}: {trend['total_emissions']:,.0f} tCO2e")
                
    except Exception as e:
        print(f"An error occurred during agent test: {e}")
