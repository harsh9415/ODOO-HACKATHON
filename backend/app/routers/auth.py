from __future__ import annotations

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from datetime import date
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.database import get_db
from app.models import (
    User,
    Company,
    EmployeeProfile,
    ResumeInfo,
    BankDetails,
    SalaryStructure,
    UserRole,
)
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserMeResponse,
    CompanyRegisterRequest,
)
from app.utils.text import normalize_login_id, get_company_initials, validate_password_strength

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    login_id = normalize_login_id(body.login_id)
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(
            (User.login_id == login_id) | (User.email == login_id),
            User.is_active == True,  # noqa: E712
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        must_change_password=user.must_change_password,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: CompanyRegisterRequest, db: AsyncSession = Depends(get_db)):
    ok, err_msg = validate_password_strength(body.password)
    if not ok:
        raise HTTPException(status_code=400, detail=err_msg)

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    company = Company(name=body.company_name, logo_url=body.logo_url)
    db.add(company)
    await db.flush()

    company_initials = get_company_initials(body.company_name)
    year = date.today().year
    login_id = f"{company_initials}ADMIN{year}0001"

    user = User(
        login_id=login_id,
        email=body.email,
        hashed_password=get_password_hash(body.password),
        role=UserRole.admin,
        must_change_password=False,
    )
    db.add(user)
    await db.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        company_id=company.id,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        department="Administration",
        date_of_joining=date.today(),
    )
    db.add(profile)
    db.add(ResumeInfo(user_id=user.id, skills=[], certifications=[]))
    db.add(BankDetails(user_id=user.id))
    db.add(SalaryStructure(user_id=user.id, month_wage=80000))
    await db.flush()
    await db.commit()

    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        must_change_password=user.must_change_password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    ok, err_msg = validate_password_strength(body.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=err_msg)

    current_user.hashed_password = get_password_hash(body.new_password)
    current_user.must_change_password = False
    await db.flush()
    return {"detail": "Password changed successfully"}


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = current_user.profile
    company_name = None
    company_logo = None
    if profile:
        from app.models import Company

        co = await db.get(Company, profile.company_id)
        if co:
            company_name = co.name
            company_logo = co.logo_url

    return UserMeResponse(
        id=current_user.id,
        login_id=current_user.login_id,
        email=current_user.email,
        role=current_user.role,
        must_change_password=current_user.must_change_password,
        email_verified=current_user.email_verified,
        first_name=profile.first_name if profile else None,
        last_name=profile.last_name if profile else None,
        profile_picture_url=profile.profile_picture_url if profile else None,
        company_name=company_name,
        company_logo_url=company_logo,
    )


@router.post("/verify-email")
async def verify_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.email_verified = True
    await db.flush()
    return {"detail": "Email verified successfully"}
