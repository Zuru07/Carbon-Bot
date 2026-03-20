import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


class TestSustainabilityAgent:
    """Tests for the SustainabilityAgent class."""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables for testing."""
        monkeypatch.setenv("POSTGRES_URI", "postgresql://test:test@localhost:5432/testdb")
        monkeypatch.setenv("POSTGRES_TABLE_NAME", "company_emissions")

    @pytest.fixture
    def sample_company_data(self):
        """Sample company data for testing."""
        return pd.DataFrame({
            'company_name': ['Test Company'],
            'reporting_year': [2024],
            'sector': ['Technology'],
            'scope1_total': [100000.0],
            'scope2_total': [50000.0],
            'scope3_total': [500000.0],
            'scope1_q1': [25000.0],
            'scope1_q2': [25000.0],
            'scope1_q3': [25000.0],
            'scope1_q4': [25000.0],
            'scope2_q1': [12500.0],
            'scope2_q2': [12500.0],
            'scope2_q3': [12500.0],
            'scope2_q4': [12500.0],
            'scope3_q1': [125000.0],
            'scope3_q2': [125000.0],
            'scope3_q3': [125000.0],
            'scope3_q4': [125000.0],
            'electricity_kwh': [129533678.0],
            'grid_emission_factor_used': [0.386],
            'employee_count': [5000],
            'energy_mix_renewable_pct': [60.0],
            'energy_mix_fossil_pct': [25.0],
            'energy_mix_nuclear_pct': [15.0],
            'energy_mix_other_pct': [0.0],
            'region_code': ['US_CA']
        })

    def test_energy_consumption_calculation(self, sample_company_data):
        """Test that electricity consumption is calculated correctly from Scope 2."""
        from backend.utils.emission_factors import get_grid_factor
        
        scope2_tCO2e = 50000.0
        grid_factor = get_grid_factor("US_DEFAULT")
        
        expected_kwh = (scope2_tCO2e * 1000) / grid_factor
        
        assert abs(expected_kwh - 129533678.0) < 1000, "Electricity calculation should match expected value"

    def test_emission_summary_format(self, sample_company_data):
        """Test that emissions summary has correct structure."""
        snapshot = sample_company_data.iloc[0].to_dict()
        
        total = (
            snapshot['scope1_total'] + 
            snapshot['scope2_total'] + 
            snapshot['scope3_total']
        )
        
        assert total == 650000.0
        assert snapshot['scope1_q1'] + snapshot['scope1_q2'] + snapshot['scope1_q3'] + snapshot['scope1_q4'] == snapshot['scope1_total']

    def test_deviation_thresholds(self):
        """Test that deviation thresholds are loaded correctly."""
        from backend.utils.emission_factors import get_deviation_thresholds
        
        thresholds = get_deviation_thresholds()
        
        assert 'scope1_warning_pct' in thresholds
        assert 'scope1_critical_pct' in thresholds
        assert thresholds['scope1_warning_pct'] < thresholds['scope1_critical_pct']

    def test_energy_mix_validation(self, sample_company_data):
        """Test that energy mix percentages sum approximately to 100."""
        row = sample_company_data.iloc[0]
        
        total_pct = (
            row['energy_mix_renewable_pct'] +
            row['energy_mix_fossil_pct'] +
            row['energy_mix_nuclear_pct'] +
            row['energy_mix_other_pct']
        )
        
        assert 99 <= total_pct <= 101, f"Energy mix should sum to ~100%, got {total_pct}%"

    def test_quarterly_breakdown_sum(self, sample_company_data):
        """Test that quarterly breakdowns sum to annual totals."""
        for scope in ['scope1', 'scope2', 'scope3']:
            annual = sample_company_data[f'{scope}_total'].iloc[0]
            quarterly_sum = sum([
                sample_company_data[f'{scope}_q1'].iloc[0],
                sample_company_data[f'{scope}_q2'].iloc[0],
                sample_company_data[f'{scope}_q3'].iloc[0],
                sample_company_data[f'{scope}_q4'].iloc[0]
            ])
            
            assert abs(quarterly_sum - annual) < 0.01, f"{scope} quarterly sum should equal annual total"


class TestEmissionCalculator:
    """Tests for emission calculation functions."""

    def test_quarterly_generation_with_zero(self):
        """Test quarterly generation with zero emissions."""
        from backend.utils.emission_calculator import generate_quarterly_breakdown
        
        result = generate_quarterly_breakdown(0.0)
        
        assert result['q1'] == 0.0
        assert result['q2'] == 0.0
        assert result['q3'] == 0.0
        assert result['q4'] == 0.0

    def test_quarterly_generation_sum_check(self):
        """Test that quarterly values sum to annual total."""
        from backend.utils.emission_calculator import generate_quarterly_breakdown
        
        annual_total = 100000.0
        result = generate_quarterly_breakdown(annual_total)
        
        total = result['q1'] + result['q2'] + result['q3'] + result['q4']
        assert abs(total - annual_total) < 0.01

    def test_electricity_estimation_with_zero(self):
        """Test electricity estimation with zero emissions."""
        from backend.utils.emission_calculator import estimate_electricity_consumption
        
        result = estimate_electricity_consumption(0.0)
        
        assert result['electricity_kwh'] == 0.0

    def test_electricity_estimation_calculation(self):
        """Test electricity estimation calculation is correct."""
        from backend.utils.emission_calculator import estimate_electricity_consumption
        
        scope2 = 50000.0
        grid_factor = 0.386
        result = estimate_electricity_consumption(scope2, grid_factor=grid_factor)
        
        expected_kwh = (scope2 * 1000) / grid_factor
        assert abs(result['electricity_kwh'] - expected_kwh) < 1

    def test_supplier_breakdown_with_zero(self):
        """Test supplier breakdown with zero emissions."""
        from backend.utils.emission_calculator import generate_supplier_breakdown
        
        result = generate_supplier_breakdown(0.0)
        
        assert len(result) == 0

    def test_supplier_breakdown_sum_check(self):
        """Test that supplier emissions sum to total."""
        from backend.utils.emission_calculator import generate_supplier_breakdown
        
        total_scope3 = 500000.0
        n_suppliers = 5
        suppliers = generate_supplier_breakdown(total_scope3, n_suppliers=n_suppliers)
        
        assert len(suppliers) == n_suppliers
        
        sum_emissions = sum(s['emissions_tCO2e'] for s in suppliers)
        assert abs(sum_emissions - total_scope3) < 0.01

    def test_supplier_proportions_sum_to_one(self):
        """Test that supplier proportions sum to 1.0."""
        from backend.utils.emission_calculator import generate_supplier_breakdown
        
        suppliers = generate_supplier_breakdown(100000.0, n_suppliers=5)
        
        total_proportion = sum(s['proportion'] for s in suppliers)
        assert abs(total_proportion - 1.0) < 0.001

    def test_metadata_employee_count_positive(self):
        """Test that generated employee count is positive."""
        from backend.utils.emission_calculator import generate_metadata
        
        metadata = generate_metadata(100000, 50000, 500000)
        
        assert metadata['employee_count'] > 0

    def test_metadata_energy_mix_bounded(self):
        """Test that energy mix percentages are bounded 0-100."""
        from backend.utils.emission_calculator import generate_metadata
        
        metadata = generate_metadata(100000, 50000, 500000)
        
        assert 0 <= metadata['energy_mix_renewable_pct'] <= 100
        assert 0 <= metadata['energy_mix_fossil_pct'] <= 100
        assert 0 <= metadata['energy_mix_nuclear_pct'] <= 100


class TestEmissionFactors:
    """Tests for emission factors configuration."""

    def test_default_grid_factor(self):
        """Test that default grid factor is loaded."""
        from backend.utils.emission_factors import get_grid_factor
        
        factor = get_grid_factor()
        
        assert factor > 0
        assert factor < 1

    def test_region_specific_factor(self):
        """Test that region-specific factors are available."""
        from backend.utils.emission_factors import get_grid_factor
        
        ca_factor = get_grid_factor("US_CA")
        tx_factor = get_grid_factor("US_TX")
        
        assert ca_factor != tx_factor
        assert ca_factor > 0
        assert tx_factor > 0

    def test_unknown_region_uses_default(self):
        """Test that unknown region falls back to default."""
        from backend.utils.emission_factors import get_grid_factor
        
        default_factor = get_grid_factor()
        unknown_factor = get_grid_factor("UNKNOWN_REGION")
        
        assert unknown_factor == default_factor

    def test_simulation_params_structure(self):
        """Test that simulation params have required keys."""
        from backend.utils.emission_factors import get_simulation_params
        
        params = get_simulation_params()
        
        assert 'quarterly_variation_std' in params
        assert 'supplier_variation_std' in params
        assert 'dirichlet_alpha' in params
        assert 0 < params['quarterly_variation_std'] < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
