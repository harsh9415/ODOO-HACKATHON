from __future__ import annotations

from typing import Any, Optional

import calendar
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_admin
from app.database import get_db
from app.models import Attendance, AttendanceStatus, EmployeeProfile, LeaveRequest, LeaveStatus, SalaryStructure, User
from app.schemas import (
    AdminDayAttendance,
    AttendanceDayRecord,
    CheckInOutResponse,
    EmployeeMonthAttendance,
    TodayStatusResponse,
)
from app.services.attendance_service import (
    compute_extra_hours,
    compute_work_hours,
    get_working_days_in_month,
)

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("/today-status", response_model=TodayStatusResponse)
async def today_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    result = await db.execute(
        select(Attendance).where(Attendance.user_id == current_user.id, Attendance.date == today)
    )
    record = result.scalar_one_or_none()
    if record and record.check_in and not record.check_out:
        return TodayStatusResponse(checked_in=True, check_in_time=record.check_in, status_dot="green")
    return TodayStatusResponse(checked_in=False, check_in_time=None, status_dot="red")


@router.post("/check-in", response_model=CheckInOutResponse)
async def check_in(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    now = datetime.now().time()

    result = await db.execute(
        select(Attendance).where(Attendance.user_id == current_user.id, Attendance.date == today)
    )
    record = result.scalar_one_or_none()

    if record and record.check_in and not record.check_out:
        raise HTTPException(status_code=400, detail="Already checked in")

    if not record:
        record = Attendance(user_id=current_user.id, date=today, status=AttendanceStatus.present)
        db.add(record)

    record.check_in = now
    record.check_out = None
    record.status = AttendanceStatus.present
    await db.flush()

    return CheckInOutResponse(
        message="Checked in successfully",
        check_in=record.check_in,
        status="present",
    )


@router.post("/check-out", response_model=CheckInOutResponse)
async def check_out(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    now = datetime.now().time()

    result = await db.execute(
        select(Attendance).where(Attendance.user_id == current_user.id, Attendance.date == today)
    )
    record = result.scalar_one_or_none()

    if not record or not record.check_in:
        raise HTTPException(status_code=400, detail="Must check in first")
    if record.check_out:
        raise HTTPException(status_code=400, detail="Already checked out")

    record.check_out = now
    break_mins = await _get_break_minutes(current_user.id, db)
    wh = compute_work_hours(record.check_in, record.check_out, break_mins)
    if wh < 4.5:
        record.status = AttendanceStatus.half_day
    else:
        record.status = AttendanceStatus.present

    await db.flush()

    return CheckInOutResponse(
        message="Checked out successfully",
        check_in=record.check_in,
        check_out=record.check_out,
        status=record.status.value,
    )


async def _get_break_minutes(user_id: int, db: AsyncSession) -> int:
    result = await db.execute(select(SalaryStructure).where(SalaryStructure.user_id == user_id))
    salary = result.scalar_one_or_none()
    return salary.break_time_minutes if salary else 60


@router.get("/my-month", response_model=EmployeeMonthAttendance)
async def my_month_attendance(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    year = year or today.year
    month = month or today.month
    break_mins = await _get_break_minutes(current_user.id, db)

    result = await db.execute(
        select(Attendance).where(
            Attendance.user_id == current_user.id,
            extract("year", Attendance.date) == year,
            extract("month", Attendance.date) == month,
        )
    )
    att_map = {r.date: r for r in result.scalars().all()}

    leave_result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.user_id == current_user.id,
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.start_date <= date(year, month, calendar.monthrange(year, month)[1]),
            LeaveRequest.end_date >= date(year, month, 1),
        )
    )
    leaves = leave_result.scalars().all()
    leave_dates: set[date] = set()
    for leave in leaves:
        d = leave.start_date
        while d <= leave.end_date:
            if d.year == year and d.month == month:
                leave_dates.add(d)
            d = date.fromordinal(d.toordinal() + 1)

    _, num_days = calendar.monthrange(year, month)
    records = []
    days_present = 0
    for day in range(1, num_days + 1):
        d = date(year, month, day)
        att = att_map.get(d)
        wh = 0.0
        eh = 0.0
        status = "absent"
        if att and att.check_in:
            wh = compute_work_hours(att.check_in, att.check_out, break_mins)
            eh = compute_extra_hours(wh)
            status = att.status.value if att.status else "present"
            if status == "half-day":
                days_present += 0.5
            else:
                days_present += 1
        elif d in leave_dates:
            status = "leave"

        records.append(
            AttendanceDayRecord(
                date=d,
                check_in=att.check_in if att else None,
                check_out=att.check_out if att else None,
                work_hours=round(wh, 2),
                extra_hours=round(eh, 2),
                status=status,
            )
        )

    salary_result = await db.execute(
        select(SalaryStructure).where(SalaryStructure.user_id == current_user.id)
    )
    salary = salary_result.scalar_one_or_none()
    wdpw = salary.working_days_per_week if salary else 5
    total_working = get_working_days_in_month(year, month, wdpw)

    return EmployeeMonthAttendance(
        year=year,
        month=month,
        days_present=days_present,
        leaves_count=len(leave_dates),
        total_working_days=total_working,
        records=records,
    )


@router.get("/admin-day", response_model=AdminDayAttendance)
async def admin_day_attendance(
    target_date: Optional[date] = Query(None, alias="date"),
    search: Optional[str] = Query(None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target = target_date or date.today()

    query = select(EmployeeProfile).options(selectinload(EmployeeProfile.user))
    if search:
        term = f"%{search}%"
        from sqlalchemy import or_

        query = query.where(
            or_(
                EmployeeProfile.first_name.ilike(term),
                EmployeeProfile.last_name.ilike(term),
            )
        )
    profiles = (await db.execute(query)).scalars().all()

    att_result = await db.execute(select(Attendance).where(Attendance.date == target))
    att_map = {a.user_id: a for a in att_result.scalars().all()}

    records = []
    for p in profiles:
        att = att_map.get(p.user_id)
        break_mins = await _get_break_minutes(p.user_id, db)
        wh = compute_work_hours(att.check_in, att.check_out, break_mins) if att else 0
        eh = compute_extra_hours(wh) if att else 0

        status = "absent"
        if att and att.check_in:
            status = att.status.value if att.status else "present"
        else:
            leave_result = await db.execute(
                select(LeaveRequest).where(
                    LeaveRequest.user_id == p.user_id,
                    LeaveRequest.status == LeaveStatus.approved,
                    LeaveRequest.start_date <= target,
                    LeaveRequest.end_date >= target,
                )
            )
            if leave_result.scalar_one_or_none():
                status = "leave"

        records.append(
            {
                "employee_name": f"{p.first_name} {p.last_name}",
                "user_id": p.user_id,
                "check_in": att.check_in.isoformat() if att and att.check_in else None,
                "check_out": att.check_out.isoformat() if att and att.check_out else None,
                "work_hours": round(wh, 2),
                "extra_hours": round(eh, 2),
                "status": status,
            }
        )

    return AdminDayAttendance(date=target, records=records)
