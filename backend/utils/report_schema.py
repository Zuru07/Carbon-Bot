import logging
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ReportingPeriod(BaseModel):
    """Defines the time period covered by the report."""
    year: int
    quarter: int | None = Field(default=None, ge=1, le=4)
    start_date: str | None = None
    end_date: str | None = None


class EmissionsTotals(BaseModel):
    """Scope 1, 2, 3 emissions totals."""
    scope1_tCO2e: float = Field(ge=0)
    scope2_tCO2e: float = Field(ge=0)
    scope3_tCO2e: float = Field(ge=0)
    total_tCO2e: float = Field(default=0, ge=0)

    def __init__(self, **data):
        if 'total_tCO2e' not in data or data.get('total_tCO2e') == 0:
            data['total_tCO2e'] = (
                data.get('scope1_tCO2e', 0) +
                data.get('scope2_tCO2e', 0) +
                data.get('scope3_tCO2e', 0)
            )
        super().__init__(**data)


class QuarterlyEmissions(BaseModel):
    """Quarterly breakdown of emissions."""
    q1: float = Field(ge=0)
    q2: float = Field(ge=0)
    q3: float = Field(ge=0)
    q4: float = Field(ge=0)

    @property
    def total(self) -> float:
        return self.q1 + self.q2 + self.q3 + self.q4


class ElectricityData(BaseModel):
    """Electricity consumption estimation."""
    electricity_kwh: float = Field(ge=0)
    grid_emission_factor_kg_per_kwh: float = Field(ge=0)
    region_code: str


class SupplierEmissions(BaseModel):
    """Individual supplier emissions breakdown."""
    supplier_id: str
    supplier_name: str
    emissions_tCO2e: float = Field(ge=0)
    proportion: float = Field(ge=0, le=1)


class EnergyMix(BaseModel):
    """Energy source mix percentages."""
    renewable_pct: float = Field(ge=0, le=100)
    fossil_pct: float = Field(ge=0, le=100)
    nuclear_pct: float = Field(ge=0, le=100)
    other_pct: float = Field(ge=0, le=100)

    @field_validator('renewable_pct', 'fossil_pct', 'nuclear_pct', 'other_pct', mode='before')
    @classmethod
    def handle_none(cls, v):
        return v if v is not None else 0.0


class CompanyMetadata(BaseModel):
    """Company metadata for the report."""
    employee_count: int = Field(ge=0)
    sector: str | None = None
    headquarters_country: str | None = None
    region_code: str | None = None


class DeviationAlert(BaseModel):
    """Alert for significant emissions changes."""
    metric: str
    previous_value: float
    current_value: float
    change_pct: float
    severity: Literal['info', 'warning', 'critical']
    message: str


class ComplianceStatus(BaseModel):
    """Compliance status information."""
    reporting_framework: str = "GHG Protocol"
    reporting_standard: str = "ISO 14064-1"
    third_party_verified: bool = False
    verification_body: str | None = None
    compliance_notes: str | None = None


class DataQuality(BaseModel):
    """Data quality indicators."""
    data_completeness_pct: float = Field(ge=0, le=100)
    simulated_data_pct: float = Field(ge=0, le=100)
    methodology: str
    data_sources: list[str]


class MethodologyNotes(BaseModel):
    """Methodology documentation."""
    scope_distribution_method: str
    supplier_breakdown_method: str
    electricity_estimation_method: str
    notes: str | None = None


class ESGReportSchema(BaseModel):
    """
    Structured ESG report schema for regulatory submissions and investor communication.
    
    This schema ensures all reports follow a consistent, parseable format
    suitable for automated compliance checking and regulatory filings.
    """
    report_id: str
    report_type: Literal['annual', 'quarterly', 'spot']
    version: str = "1.0"
    
    company_name: str
    reporting_period: ReportingPeriod
    
    emissions_summary: EmissionsTotals
    quarterly_breakdown: dict[str, QuarterlyEmissions] | None = None
    electricity_consumption: ElectricityData | None = None
    supplier_emissions: list[SupplierEmissions] | None = None
    
    company_metadata: CompanyMetadata | None = None
    energy_mix: EnergyMix | None = None
    
    compliance_status: ComplianceStatus
    deviation_alerts: list[DeviationAlert] | None = None
    
    data_quality: DataQuality
    methodology: MethodologyNotes
    
    data_sources: list[str]
    generated_at: datetime
    generated_by: str = "Carbon-bot"
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "ESG-2024-001",
                "report_type": "annual",
                "version": "1.0",
                "company_name": "Example Corp",
                "reporting_period": {
                    "year": 2024,
                    "quarter": None
                },
                "emissions_summary": {
                    "scope1_tCO2e": 100000.0,
                    "scope2_tCO2e": 50000.0,
                    "scope3_tCO2e": 500000.0,
                    "total_tCO2e": 650000.0
                },
                "compliance_status": {
                    "reporting_framework": "GHG Protocol",
                    "reporting_standard": "ISO 14064-1",
                    "third_party_verified": False
                },
                "data_quality": {
                    "data_completeness_pct": 95.0,
                    "simulated_data_pct": 25.0,
                    "methodology": "Hybrid actual/simulated",
                    "data_sources": ["Company records", "Simulated quarterly data"]
                },
                "data_sources": ["Company records", "Simulated quarterly data"],
                "generated_at": "2024-01-15T10:30:00",
                "generated_by": "Carbon-bot"
            }
        }


def validate_report(report: dict) -> tuple[bool, list[str]]:
    """
    Validates a report dictionary against the ESGReportSchema.
    
    Args:
        report: Dictionary representation of an ESG report
        
    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    errors = []
    
    required_fields = [
        'report_id', 'report_type', 'company_name', 'reporting_period',
        'emissions_summary', 'compliance_status', 'data_quality',
        'methodology', 'data_sources', 'generated_at'
    ]
    
    for field in required_fields:
        if field not in report:
            errors.append(f"Missing required field: {field}")
    
    if 'reporting_period' in report:
        period = report['reporting_period']
        if isinstance(period, dict):
            if 'year' not in period:
                errors.append("reporting_period must include 'year'")
    
    if 'emissions_summary' in report:
        summary = report['emissions_summary']
        if isinstance(summary, dict):
            for scope in ['scope1_tCO2e', 'scope2_tCO2e', 'scope3_tCO2e']:
                if scope in summary and summary[scope] < 0:
                    errors.append(f"{scope} cannot be negative")
    
    return len(errors) == 0, errors


def create_report_from_snapshot(
    company_name: str,
    snapshot: dict,
    report_id: str | None = None,
    report_type: str = "annual",
    alerts: list[dict] | None = None
) -> ESGReportSchema:
    """
    Creates a structured ESG report from company snapshot data.
    
    Args:
        company_name: Name of the company
        snapshot: Company data snapshot from SustainabilityAgent
        report_id: Optional report ID (generated if not provided)
        report_type: Type of report (annual, quarterly, spot)
        alerts: Optional list of deviation alerts
        
    Returns:
        ESGReportSchema instance
    """
    if report_id is None:
        report_id = f"ESG-{snapshot.get('reporting_year', 2024)}-{company_name[:10].replace(' ', '-')}"
    
    reporting_period = ReportingPeriod(
        year=snapshot.get('reporting_year', 2024),
        quarter=None
    )
    
    emissions_summary = EmissionsTotals(
        scope1_tCO2e=snapshot.get('scope1_total', 0),
        scope2_tCO2e=snapshot.get('scope2_total', 0),
        scope3_tCO2e=snapshot.get('scope3_total', 0)
    )
    
    electricity = None
    if snapshot.get('electricity_kwh'):
        electricity = ElectricityData(
            electricity_kwh=snapshot.get('electricity_kwh', 0),
            grid_emission_factor_kg_per_kwh=snapshot.get('grid_emission_factor_used', 0.386),
            region_code=snapshot.get('region_code', 'US_DEFAULT')
        )
    
    company_metadata = CompanyMetadata(
        employee_count=snapshot.get('employee_count', 0),
        sector=snapshot.get('sector'),
        headquarters_country=snapshot.get('headquarters_country'),
        region_code=snapshot.get('region_code')
    )
    
    energy_mix = None
    if snapshot.get('energy_mix_renewable_pct') is not None:
        energy_mix = EnergyMix(
            renewable_pct=snapshot.get('energy_mix_renewable_pct', 0),
            fossil_pct=snapshot.get('energy_mix_fossil_pct', 0),
            nuclear_pct=snapshot.get('energy_mix_nuclear_pct', 0),
            other_pct=snapshot.get('energy_mix_other_pct', 0)
        )
    
    deviation_alerts = None
    if alerts:
        deviation_alerts = [
            DeviationAlert(
                metric=a.get('metric', 'unknown'),
                previous_value=a.get('previous_value', 0),
                current_value=a.get('current_value', 0),
                change_pct=a.get('change_pct', 0),
                severity=a.get('severity', 'info'),
                message=a.get('message', '')
            )
            for a in alerts
        ]
    
    compliance_status = ComplianceStatus(
        reporting_framework="GHG Protocol",
        reporting_standard="ISO 14064-1",
        third_party_verified=False
    )
    
    simulated_pct = 25.0 if snapshot.get('is_simulated') else 0.0
    data_quality = DataQuality(
        data_completeness_pct=95.0,
        simulated_data_pct=simulated_pct,
        methodology="Hybrid actual/simulated" if simulated_pct > 0 else "Actual reported",
        data_sources=["Company records"]
    )
    
    methodology = MethodologyNotes(
        scope_distribution_method=snapshot.get('scope_distribution_method', 'unknown'),
        supplier_breakdown_method=snapshot.get('scope3_supplier_method', 'unknown'),
        electricity_estimation_method="Grid emission factor back-calculation"
    )
    
    data_sources = ["Company records"]
    if snapshot.get('is_simulated'):
        data_sources.append("Simulated quarterly data")
    
    report = ESGReportSchema(
        report_id=report_id,
        report_type=report_type,
        company_name=company_name,
        reporting_period=reporting_period,
        emissions_summary=emissions_summary,
        electricity_consumption=electricity,
        company_metadata=company_metadata,
        energy_mix=energy_mix,
        compliance_status=compliance_status,
        deviation_alerts=deviation_alerts,
        data_quality=data_quality,
        methodology=methodology,
        data_sources=data_sources,
        generated_at=datetime.now(),
        generated_by="Carbon-bot"
    )
    
    return report


if __name__ == "__main__":
    print("=== Testing ESG Report Schema ===\n")
    
    sample_snapshot = {
        'company_name': 'Test Corp',
        'reporting_year': 2024,
        'sector': 'Technology',
        'scope1_total': 100000.0,
        'scope2_total': 50000.0,
        'scope3_total': 500000.0,
        'electricity_kwh': 129533678.0,
        'grid_emission_factor_used': 0.386,
        'employee_count': 5000,
        'energy_mix_renewable_pct': 60.0,
        'energy_mix_fossil_pct': 25.0,
        'energy_mix_nuclear_pct': 15.0,
        'energy_mix_other_pct': 0.0,
        'scope_distribution_method': 'normal_distribution',
        'scope3_supplier_method': 'dirichlet',
        'is_simulated': True,
        'region_code': 'US_CA'
    }
    
    report = create_report_from_snapshot(
        'Test Corp',
        sample_snapshot,
        report_type='annual'
    )
    
    print(f"Report ID: {report.report_id}")
    print(f"Company: {report.company_name}")
    print(f"Total Emissions: {report.emissions_summary.total_tCO2e:,.0f} tCO2e")
    print(f"Electricity: {report.electricity_consumption.electricity_kwh:,.0f} kWh")
    print(f"Employees: {report.company_metadata.employee_count:,}")
    print(f"Energy Mix: {report.energy_mix.renewable_pct:.1f}% renewable")
    
    print("\n--- JSON Output ---")
    print(report.model_dump_json(indent=2))
    
    is_valid, errors = validate_report(report.model_dump())
    print(f"\nValidation: {'PASSED' if is_valid else 'FAILED'}")
    if errors:
        print(f"Errors: {errors}")
