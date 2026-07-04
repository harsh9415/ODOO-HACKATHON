from __future__ import annotations

"""Payroll and salary component calculations."""

from dataclasses import dataclass


@dataclass
class SalaryComponents:
    basic: float
    hra: float
    standard_allowance: float
    performance_bonus: float
    lta: float
    fixed_allowance: float
    pf_employee: float
    pf_employer: float
    professional_tax: float
    net_take_home: float

    def to_dict(self) -> dict:
        return {
            "basic": round(self.basic, 2),
            "hra": round(self.hra, 2),
            "standard_allowance": round(self.standard_allowance, 2),
            "performance_bonus": round(self.performance_bonus, 2),
            "lta": round(self.lta, 2),
            "fixed_allowance": round(self.fixed_allowance, 2),
            "pf_employee": round(self.pf_employee, 2),
            "pf_employer": round(self.pf_employer, 2),
            "professional_tax": round(self.professional_tax, 2),
            "net_take_home": round(self.net_take_home, 2),
        }


def calculate_salary_components(
    month_wage: float,
    basic_pct: float = 50.0,
    hra_pct: float = 50.0,
    standard_allowance_pct: float = 8.33,
    performance_bonus_pct: float = 8.33,
    lta_pct: float = 8.33,
    pf_employee_pct: float = 12.0,
    pf_employer_pct: float = 12.0,
    professional_tax: float = 200.0,
) -> SalaryComponents:
    """
    Calculate salary components.
    - Basic, Standard Allowance, Performance Bonus, LTA: % of month_wage
    - HRA: % of Basic (not of wage)
    - Fixed Allowance: remainder = wage - sum(other components)
    - PF: % of Basic
    """
    basic = month_wage * (basic_pct / 100)
    hra = basic * (hra_pct / 100)
    standard_allowance = month_wage * (standard_allowance_pct / 100)
    performance_bonus = month_wage * (performance_bonus_pct / 100)
    lta = month_wage * (lta_pct / 100)

    other_sum = basic + hra + standard_allowance + performance_bonus + lta
    fixed_allowance = max(0, month_wage - other_sum)

    pf_employee = basic * (pf_employee_pct / 100)
    pf_employer = basic * (pf_employer_pct / 100)

    gross = basic + hra + standard_allowance + performance_bonus + lta + fixed_allowance
    net_take_home = gross - pf_employee - professional_tax

    return SalaryComponents(
        basic=basic,
        hra=hra,
        standard_allowance=standard_allowance,
        performance_bonus=performance_bonus,
        lta=lta,
        fixed_allowance=fixed_allowance,
        pf_employee=pf_employee,
        pf_employer=pf_employer,
        professional_tax=professional_tax,
        net_take_home=net_take_home,
    )


def validate_components_within_wage(
    month_wage: float,
    basic_pct: float,
    hra_pct: float,
    standard_allowance_pct: float,
    performance_bonus_pct: float,
    lta_pct: float,
) -> tuple[bool, str]:
    """Validate that sum of all components does not exceed monthly wage."""
    components = calculate_salary_components(
        month_wage=month_wage,
        basic_pct=basic_pct,
        hra_pct=hra_pct,
        standard_allowance_pct=standard_allowance_pct,
        performance_bonus_pct=performance_bonus_pct,
        lta_pct=lta_pct,
    )
    total = (
        components.basic
        + components.hra
        + components.standard_allowance
        + components.performance_bonus
        + components.lta
        + components.fixed_allowance
    )
    if total > month_wage + 0.01:
        return False, f"Total components ({total:.2f}) exceed monthly wage ({month_wage:.2f})"
    return True, ""
