from __future__ import annotations

from typing import Any, Optional

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_admin
from app.core.security import get_password_hash
from app.database import get_db
from app.models import (
    BankDetails,
    Company,
    EmployeeProfile,
    ResumeInfo,
    SalaryStructure,
    User,
    UserRole,
    Document,
)
from app.schemas import (
    BankDetailsUpdate,
    CreateEmployeeRequest,
    CreateEmployeeResponse,
    EmployeeListItem,
    PrivateInfoResponse,
    PrivateInfoUpdate,
    ProfileHeader,
    ResumeResponse,
    ResumeUpdate,
    SalaryStructureResponse,
    SalaryStructureUpdate,
    DocumentResponse,
    DocumentCreate,
)
from app.services.attendance_service import get_employee_status_for_today
from app.services.login_id_generator import generate_login_id
from app.services.password_generator import generate_temp_password
from app.services.payroll_calculator import calculate_salary_components, validate_components_within_wage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeListItem])
async def list_employees(
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(EmployeeProfile)
        .options(selectinload(EmployeeProfile.user))
        .where(EmployeeProfile.user.has(User.is_active == True))  # noqa: E712
    )
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                EmployeeProfile.first_name.ilike(term),
                EmployeeProfile.last_name.ilike(term),
                EmployeeProfile.department.ilike(term),
            )
        )

    result = await db.execute(query)
    profiles = result.scalars().all()

    items = []
    for p in profiles:
        status_icon = await get_employee_status_for_today(p.user_id, db)
        items.append(
            EmployeeListItem(
                id=p.id,
                user_id=p.user_id,
                first_name=p.first_name,
                last_name=p.last_name,
                full_name=f"{p.first_name} {p.last_name}",
                department=p.department,
                profile_picture_url=p.profile_picture_url,
                status_icon=status_icon,
            )
        )
    return items


@router.post("", response_model=CreateEmployeeResponse, status_code=201)
async def create_employee(
    body: CreateEmployeeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    company = await db.get(Company, body.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    year = body.date_of_joining.year
    login_id = await generate_login_id(
        body.first_name, body.last_name, company.name, year, db
    )
    temp_password = generate_temp_password()
    logger.info("Generated temp password for %s: %s", login_id, temp_password)
    print(f"[HRMS] New employee {login_id} temp password: {temp_password}")

    user = User(
        login_id=login_id,
        email=body.email,
        hashed_password=get_password_hash(temp_password),
        role=UserRole.employee,
        must_change_password=True,
    )
    db.add(user)
    await db.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        company_id=body.company_id,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        department=body.department,
        manager_id=body.manager_id,
        location=body.location,
        date_of_joining=body.date_of_joining,
    )
    db.add(profile)
    db.add(ResumeInfo(user_id=user.id, skills=[], certifications=[]))
    db.add(BankDetails(user_id=user.id))
    db.add(SalaryStructure(user_id=user.id, month_wage=50000))
    await db.flush()

    return CreateEmployeeResponse(
        id=user.id,
        login_id=login_id,
        email=body.email,
        temporary_password=temp_password,
        first_name=body.first_name,
        last_name=body.last_name,
    )


async def _get_profile_or_404(user_id: int, db: AsyncSession) -> EmployeeProfile:
    result = await db.execute(
        select(EmployeeProfile)
        .options(
            selectinload(EmployeeProfile.user),
            selectinload(EmployeeProfile.manager).selectinload(User.profile),
        )
        .where(EmployeeProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employee not found")
    return profile


def _build_header(profile: EmployeeProfile) -> ProfileHeader:
    manager_name = None
    if profile.manager and profile.manager.profile:
        mp = profile.manager.profile
        manager_name = f"{mp.first_name} {mp.last_name}"
    return ProfileHeader(
        login_id=profile.user.login_id,
        email=profile.user.email,
        phone=profile.phone,
        department=profile.department,
        manager_name=manager_name,
        location=profile.location,
        first_name=profile.first_name,
        last_name=profile.last_name,
        profile_picture_url=profile.profile_picture_url,
    )


def _can_edit_profile(current_user: User, target_user_id: int) -> bool:
    return current_user.role == UserRole.admin or current_user.id == target_user_id


@router.get("/{user_id}/resume", response_model=ResumeResponse)
async def get_resume(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_profile_or_404(user_id, db)
    result = await db.execute(select(ResumeInfo).where(ResumeInfo.user_id == user_id))
    resume = result.scalar_one_or_none()
    if not resume:
        return ResumeResponse(skills=[], certifications=[])
    return ResumeResponse(
        about=resume.about,
        job_love_note=resume.job_love_note,
        interests=resume.interests,
        skills=resume.skills or [],
        certifications=resume.certifications or [],
    )


@router.put("/{user_id}/resume", response_model=ResumeResponse)
async def update_resume(
    user_id: int,
    body: ResumeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _can_edit_profile(current_user, user_id):
        raise HTTPException(status_code=403, detail="Not authorized to edit this profile")
    await _get_profile_or_404(user_id, db)
    result = await db.execute(select(ResumeInfo).where(ResumeInfo.user_id == user_id))
    resume = result.scalar_one_or_none()
    if not resume:
        resume = ResumeInfo(user_id=user_id, skills=[], certifications=[])
        db.add(resume)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(resume, field, value)
    await db.flush()
    return ResumeResponse(
        about=resume.about,
        job_love_note=resume.job_love_note,
        interests=resume.interests,
        skills=resume.skills or [],
        certifications=resume.certifications or [],
    )


@router.get("/{user_id}/private-info", response_model=PrivateInfoResponse)
async def get_private_info(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = await _get_profile_or_404(user_id, db)
    bank_result = await db.execute(select(BankDetails).where(BankDetails.user_id == user_id))
    bank = bank_result.scalar_one_or_none()
    return PrivateInfoResponse(
        header=_build_header(profile),
        dob=profile.dob,
        residing_address=profile.residing_address,
        nationality=profile.nationality,
        personal_email=profile.personal_email,
        gender=profile.gender,
        marital_status=profile.marital_status,
        date_of_joining=profile.date_of_joining,
        emp_code=profile.emp_code,
        bank_details=BankDetailsUpdate(
            account_number=bank.account_number if bank else None,
            bank_name=bank.bank_name if bank else None,
            ifsc_code=bank.ifsc_code if bank else None,
            pan_no=bank.pan_no if bank else None,
            uan_no=bank.uan_no if bank else None,
        )
        if bank
        else None,
    )


@router.put("/{user_id}/private-info", response_model=PrivateInfoResponse)
async def update_private_info(
    user_id: int,
    body: PrivateInfoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin = current_user.role == UserRole.admin
    is_self = current_user.id == user_id
    if not is_admin and not is_self:
        raise HTTPException(status_code=403, detail="Not authorized")

    profile = await _get_profile_or_404(user_id, db)
    data = body.model_dump(exclude_unset=True)
    bank_data = data.pop("bank_details", None)

    admin_only = {"department", "manager_id", "location", "date_of_joining", "emp_code"}
    if not is_admin:
        for field in admin_only:
            data.pop(field, None)

    for field, value in data.items():
        setattr(profile, field, value)

    if bank_data:
        bank_result = await db.execute(select(BankDetails).where(BankDetails.user_id == user_id))
        bank_obj = bank_result.scalar_one_or_none()
        if not bank_obj:
            bank_obj = BankDetails(user_id=user_id)
            db.add(bank_obj)
        for field, value in bank_data.items():
            if value is not None:
                setattr(bank_obj, field, value)

    await db.flush()
    return await get_private_info(user_id, db, current_user)


@router.get("/{user_id}/salary", response_model=SalaryStructureResponse)
async def get_salary(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin = current_user.role == UserRole.admin
    is_self = current_user.id == user_id
    if not is_admin and not is_self:
        raise HTTPException(status_code=403, detail="Not authorized to view salary")

    result = await db.execute(select(SalaryStructure).where(SalaryStructure.user_id == user_id))
    salary = result.scalar_one_or_none()
    if not salary:
        raise HTTPException(status_code=404, detail="Salary structure not found")

    components = calculate_salary_components(
        month_wage=salary.month_wage,
        basic_pct=salary.basic_pct,
        hra_pct=salary.hra_pct,
        standard_allowance_pct=salary.standard_allowance_pct,
        performance_bonus_pct=salary.performance_bonus_pct,
        lta_pct=salary.lta_pct,
        pf_employee_pct=salary.pf_employee_pct,
        pf_employer_pct=salary.pf_employer_pct,
        professional_tax=salary.professional_tax,
    )

    return SalaryStructureResponse(
        month_wage=salary.month_wage,
        yearly_wage=salary.month_wage * 12,
        working_days_per_week=salary.working_days_per_week,
        break_time_hours=salary.break_time_minutes / 60,
        basic_pct=salary.basic_pct,
        hra_pct=salary.hra_pct,
        standard_allowance_pct=salary.standard_allowance_pct,
        performance_bonus_pct=salary.performance_bonus_pct,
        lta_pct=salary.lta_pct,
        pf_employee_pct=salary.pf_employee_pct,
        pf_employer_pct=salary.pf_employer_pct,
        professional_tax=salary.professional_tax,
        components=components.to_dict(),
        editable=is_admin,
    )


@router.put("/{user_id}/salary", response_model=SalaryStructureResponse)
async def update_salary(
    user_id: int,
    body: SalaryStructureUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    valid, err = validate_components_within_wage(
        body.month_wage,
        body.basic_pct,
        body.hra_pct,
        body.standard_allowance_pct,
        body.performance_bonus_pct,
        body.lta_pct,
    )
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    result = await db.execute(select(SalaryStructure).where(SalaryStructure.user_id == user_id))
    salary = result.scalar_one_or_none()
    if not salary:
        salary = SalaryStructure(user_id=user_id)
        db.add(salary)

    for field, value in body.model_dump().items():
        if field == "break_time_minutes":
            setattr(salary, field, value)
        else:
            setattr(salary, field, value)

    await db.flush()
    return await get_salary(user_id, db, admin)


@router.get("/{user_id}/documents", response_model=list[DocumentResponse])
async def get_documents(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these documents")
    result = await db.execute(select(Document).where(Document.user_id == user_id))
    return result.scalars().all()


@router.post("/{user_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    user_id: int,
    body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to add documents for this user")
    doc = Document(
        user_id=user_id,
        name=body.name,
        file_url=body.file_url,
        file_type=body.file_type,
    )
    db.add(doc)
    await db.flush()
    return doc


@router.delete("/{user_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    user_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    result = await db.execute(
        select(Document).where(Document.user_id == user_id, Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.flush()
