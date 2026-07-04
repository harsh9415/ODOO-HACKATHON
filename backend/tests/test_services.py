import pytest

from app.services.login_id_generator import build_login_id
from app.services.password_generator import generate_temp_password
from app.services.payroll_calculator import calculate_salary_components, validate_components_within_wage
from app.utils.text import normalize_login_id


class TestLoginIdGenerator:
    def test_build_login_id_example(self):
        result = build_login_id("John", "Dodo", "Odoo India", 2022, 1)
        assert result == "OIJODO20220001"

    def test_build_login_id_serial_padding(self):
        result = build_login_id("Jane", "Smith", "Acme Corp", 2024, 42)
        assert result == "ACJASM20240042"

    def test_short_name_padding(self):
        result = build_login_id("A", "B", "Test Co", 2025, 1)
        assert result.startswith("TCAXBX2025")


class TestPasswordGenerator:
    def test_length(self):
        pwd = generate_temp_password(12)
        assert len(pwd) == 12

    def test_has_mixed_chars(self):
        pwd = generate_temp_password(12)
        assert any(c.islower() for c in pwd)
        assert any(c.isupper() for c in pwd)
        assert any(c.isdigit() for c in pwd)


class TestPayrollCalculator:
    def test_example_from_spec(self):
        components = calculate_salary_components(month_wage=50000, basic_pct=50, hra_pct=50)
        assert components.basic == 25000
        assert components.hra == 12500

    def test_fixed_allowance_is_remainder(self):
        components = calculate_salary_components(month_wage=50000)
        total = (
            components.basic
            + components.hra
            + components.standard_allowance
            + components.performance_bonus
            + components.lta
            + components.fixed_allowance
        )
        assert abs(total - 50000) < 0.01

    def test_validation_passes(self):
        valid, msg = validate_components_within_wage(50000, 50, 50, 8.33, 8.33, 8.33)
        assert valid is True
        assert msg == ""

    def test_pf_based_on_basic(self):
        components = calculate_salary_components(month_wage=50000, basic_pct=50, pf_employee_pct=12)
        assert components.pf_employee == 3000  # 12% of 25000


class TestLoginIdNormalization:
    def test_normalize_standard_login_id(self):
        assert normalize_login_id("OIADMIN20220001") == "OIADMIN20220001"

    def test_normalize_lowercase_login_id(self):
        assert normalize_login_id("oiadmin20220001") == "OIADMIN20220001"

    def test_normalize_zero_instead_of_o_typo(self):
        assert normalize_login_id("0IADMIN20220001") == "OIADMIN20220001"
        assert normalize_login_id("0iadmin20220001") == "OIADMIN20220001"

    def test_normalize_whitespace(self):
        assert normalize_login_id("  0iadmin20220001  ") == "OIADMIN20220001"

    def test_normalize_email(self):
        assert normalize_login_id("ADMIN@odooindia.com") == "admin@odooindia.com"
        assert normalize_login_id("  admin@odooindia.com  ") == "admin@odooindia.com"
