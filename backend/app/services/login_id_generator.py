"""Generate unique login IDs for employees."""

from __future__ import annotations

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.text import get_company_initials, get_name_initials


def build_login_id(
    first_name: str,
    last_name: str,
    company_name: str,
    year_of_joining: int,
    serial_number: int,
) -> str:
    """Pure function to build login ID — unit-testable without DB."""
    company_initials = get_company_initials(company_name)
    name_initials = get_name_initials(first_name, last_name)
    serial = str(serial_number).zfill(4)
    return f"{company_initials}{name_initials}{year_of_joining}{serial}"


async def generate_login_id(
    first_name: str,
    last_name: str,
    company_name: str,
    year_of_joining: int,
    db: AsyncSession,
) -> str:
    """Generate login ID with DB-backed serial number per calendar year."""
    from app.models import EmployeeProfile

    result = await db.execute(
        select(func.count())
        .select_from(EmployeeProfile)
        .where(extract("year", EmployeeProfile.date_of_joining) == year_of_joining)
    )
    count = result.scalar() or 0
    serial_number = count + 1
    return build_login_id(first_name, last_name, company_name, year_of_joining, serial_number)
