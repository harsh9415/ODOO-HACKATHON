from __future__ import annotations

from typing import Any, Optional

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_admin
from app.database import get_db
from app.models import EmployeeProfile, LeaveRequest, LeaveStatus, LeaveType, User, UserRole
from app.schemas import (
    LeaveBalanceResponse,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveReviewRequest,
)

router = APIRouter(prefix="/leave", tags=["leave"])

PAID_ALLOCATION = 24
SICK_ALLOCATION = 7


def _leave_days(start: date, end: date) -> float:
    return (end - start).days + 1


async def _compute_balance(user_id: int, leave_type: LeaveType, db: AsyncSession) -> float:
    allocation = PAID_ALLOCATION if leave_type == LeaveType.paid else SICK_ALLOCATION
    if leave_type == LeaveType.unpaid:
        return 0

    result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status == LeaveStatus.approved,
        )
    )
    used = sum(_leave_days(r.start_date, r.end_date) for r in result.scalars().all())
    return max(0, allocation - used)


def _to_response(leave: LeaveRequest, profile: EmployeeProfile | None) -> LeaveRequestResponse:
    name = f"{profile.first_name} {profile.last_name}" if profile else "Unknown"
    return LeaveRequestResponse(
        id=leave.id,
        user_id=leave.user_id,
        employee_name=name,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        days=_leave_days(leave.start_date, leave.end_date),
        remarks=leave.remarks,
        status=leave.status,
        attachment_url=leave.attachment_url,
        admin_comment=leave.admin_comment,
        created_at=leave.created_at,
    )


@router.get("/balance", response_model=LeaveBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    paid = await _compute_balance(current_user.id, LeaveType.paid, db)
    sick = await _compute_balance(current_user.id, LeaveType.sick, db)
    return LeaveBalanceResponse(paid_time_off=paid, sick_time_off=sick)


@router.post("", response_model=LeaveRequestResponse, status_code=201)
async def apply_leave(
    body: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    leave = LeaveRequest(
        user_id=current_user.id,
        leave_type=body.leave_type,
        start_date=body.start_date,
        end_date=body.end_date,
        remarks=body.remarks,
        attachment_url=body.attachment_url,
        status=LeaveStatus.pending,
    )
    db.add(leave)
    await db.flush()

    profile = current_user.profile
    return _to_response(leave, profile)


@router.get("", response_model=list[LeaveRequestResponse])
async def list_leaves(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.admin:
        result = await db.execute(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.user).selectinload(User.profile))
            .order_by(LeaveRequest.created_at.desc())
        )
        leaves = result.scalars().all()
        return [_to_response(l, l.user.profile if l.user else None) for l in leaves]

    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.user_id == current_user.id)
        .order_by(LeaveRequest.created_at.desc())
    )
    leaves = result.scalars().all()
    return [_to_response(l, current_user.profile) for l in leaves]


@router.patch("/{leave_id}/review", response_model=LeaveRequestResponse)
async def review_leave(
    leave_id: int,
    body: LeaveReviewRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.status not in (LeaveStatus.approved, LeaveStatus.rejected):
        raise HTTPException(status_code=400, detail="Status must be Approved or Rejected")

    result = await db.execute(
        select(LeaveRequest)
        .options(selectinload(LeaveRequest.user).selectinload(User.profile))
        .where(LeaveRequest.id == leave_id)
    )
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave.status = body.status
    leave.admin_comment = body.admin_comment
    leave.reviewed_by = admin.id
    await db.flush()

    return _to_response(leave, leave.user.profile if leave.user else None)


@router.get("/calendar/{year}", response_model=list[dict])
async def calendar_markers(
    year: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return leave dates with status for calendar view."""
    user_id = current_user.id
    result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.start_date <= date(year, 12, 31),
            LeaveRequest.end_date >= date(year, 1, 1),
        )
    )
    markers = []
    for leave in result.scalars().all():
        d = leave.start_date
        while d <= leave.end_date:
            if d.year == year:
                status_map = {
                    LeaveStatus.approved: "approved",
                    LeaveStatus.rejected: "rejected",
                    LeaveStatus.pending: "pending",
                }
                markers.append(
                    {
                        "date": d.isoformat(),
                        "leave_type": leave.leave_type.value,
                        "status": status_map[leave.status],
                    }
                )
            d = date.fromordinal(d.toordinal() + 1)
    return markers
