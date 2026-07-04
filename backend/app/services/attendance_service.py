from __future__ import annotations

from typing import Any, Optional

"""Attendance and payroll-related calculations."""

import calendar
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Attendance, AttendanceStatus, LeaveRequest, LeaveStatus, LeaveType


def compute_work_hours(check_in: Optional[time], check_out: Optional[time], break_minutes: int = 60) -> float:
    if not check_in or not check_out:
        return 0.0
    ci = datetime.combine(date.today(), check_in)
    co = datetime.combine(date.today(), check_out)
    if co < ci:
        co += timedelta(days=1)
    total_minutes = (co - ci).total_seconds() / 60 - break_minutes
    return max(0, total_minutes / 60)


def compute_extra_hours(work_hours: float, standard_hours: Optional[float] = None) -> float:
    std = standard_hours or settings.STANDARD_DAILY_HOURS
    return max(0, work_hours - std)


def get_working_days_in_month(year: int, month: int, working_days_per_week: int = 5) -> int:
    """Count working days in a month (Mon-Fri for 5-day week)."""
    _, num_days = calendar.monthrange(year, month)
    count = 0
    for day in range(1, num_days + 1):
        d = date(year, month, day)
        weekday = d.weekday()
        if working_days_per_week == 5 and weekday < 5:
            count += 1
        elif working_days_per_week == 6 and weekday < 6:
            count += 1
    return count


async def compute_payable_days(
    user_id: int,
    year: int,
    month: int,
    db: AsyncSession,
    working_days_per_week: int = 5,
) -> dict:
    """Compute payable days for payroll: working days - unpaid leave - unexplained absences."""
    total_working = get_working_days_in_month(year, month, working_days_per_week)

    leave_result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.start_date <= date(year, month, calendar.monthrange(year, month)[1]),
            LeaveRequest.end_date >= date(year, month, 1),
        )
    )
    leaves = leave_result.scalars().all()

    unpaid_leave_days = 0
    paid_leave_days = 0
    for leave in leaves:
        start = max(leave.start_date, date(year, month, 1))
        end = min(leave.end_date, date(year, month, calendar.monthrange(year, month)[1]))
        days = (end - start).days + 1
        if leave.leave_type == LeaveType.unpaid:
            unpaid_leave_days += days
        else:
            paid_leave_days += days

    att_result = await db.execute(
        select(Attendance).where(
            Attendance.user_id == user_id,
            extract("year", Attendance.date) == year,
            extract("month", Attendance.date) == month,
        )
    )
    records = att_result.scalars().all()
    present_days = sum(
        1.0 if r.status == AttendanceStatus.present else 0.5 if r.status == AttendanceStatus.half_day else 0.0
        for r in records if r.check_in
    )

    unexplained_absent = max(0, total_working - present_days - paid_leave_days - unpaid_leave_days)
    payable = total_working - unpaid_leave_days - unexplained_absent

    return {
        "total_working_days": total_working,
        "present_days": present_days,
        "paid_leave_days": paid_leave_days,
        "unpaid_leave_days": unpaid_leave_days,
        "unexplained_absent_days": unexplained_absent,
        "payable_days": payable,
    }


async def get_employee_status_for_today(user_id: int, db: AsyncSession) -> str:
    """Return status icon: present, leave, or absent."""
    today = date.today()

    leave_result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
        )
    )
    if leave_result.scalar_one_or_none():
        return "leave"

    att_result = await db.execute(
        select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.date == today,
            Attendance.check_in.isnot(None),
            Attendance.check_out.is_(None),
        )
    )
    if att_result.scalar_one_or_none():
        return "present"

    att_checked = await db.execute(
        select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.date == today,
            Attendance.check_in.isnot(None),
        )
    )
    if att_checked.scalar_one_or_none():
        return "present"

    return "absent"
