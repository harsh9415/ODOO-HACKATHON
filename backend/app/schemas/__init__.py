from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field

from app.models import AttendanceStatus, LeaveStatus, LeaveType, UserRole


# Auth
class LoginRequest(BaseModel):
    login_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str


# Employee creation
class CreateEmployeeRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    date_of_joining: date
    company_id: int = 1


class CreateEmployeeResponse(BaseModel):
    id: int
    login_id: str
    email: str
    temporary_password: str
    first_name: str
    last_name: str
    message: str = "Employee created. Share the temporary password securely."


# Employee list
class EmployeeListItem(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    full_name: str
    department: Optional[str]
    profile_picture_url: Optional[str]
    status_icon: str  # present, leave, absent

    class Config:
        from_attributes = True


# Profile
class ProfileHeader(BaseModel):
    login_id: str
    email: str
    phone: Optional[str]
    department: Optional[str]
    manager_name: Optional[str]
    location: Optional[str]
    first_name: str
    last_name: str
    profile_picture_url: Optional[str]


class ResumeUpdate(BaseModel):
    about: Optional[str] = None
    job_love_note: Optional[str] = None
    interests: Optional[str] = None
    skills: Optional[list[str]] = None
    certifications: Optional[list[str]] = None


class ResumeResponse(ResumeUpdate):
    pass


class BankDetailsUpdate(BaseModel):
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    pan_no: Optional[str] = None
    uan_no: Optional[str] = None


class PrivateInfoUpdate(BaseModel):
    dob: Optional[date] = None
    residing_address: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    date_of_joining: Optional[date] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    emp_code: Optional[str] = None
    bank_details: Optional[BankDetailsUpdate] = None


class PrivateInfoResponse(BaseModel):
    header: ProfileHeader
    dob: Optional[date]
    residing_address: Optional[str]
    nationality: Optional[str]
    personal_email: Optional[str]
    gender: Optional[str]
    marital_status: Optional[str]
    date_of_joining: Optional[date]
    emp_code: Optional[str]
    bank_details: Optional[BankDetailsUpdate]


class SalaryStructureUpdate(BaseModel):
    month_wage: float = Field(gt=0)
    working_days_per_week: int = 5
    break_time_minutes: int = 60
    basic_pct: float = 50.0
    hra_pct: float = 50.0
    standard_allowance_pct: float = 8.33
    performance_bonus_pct: float = 8.33
    lta_pct: float = 8.33
    pf_employee_pct: float = 12.0
    pf_employer_pct: float = 12.0
    professional_tax: float = 200.0


class SalaryStructureResponse(BaseModel):
    month_wage: float
    yearly_wage: float
    working_days_per_week: int
    break_time_hours: float
    basic_pct: float
    hra_pct: float
    standard_allowance_pct: float
    performance_bonus_pct: float
    lta_pct: float
    pf_employee_pct: float
    pf_employer_pct: float
    professional_tax: float
    components: dict[str, float]
    editable: bool = False


# Attendance
class CheckInOutResponse(BaseModel):
    message: str
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str


class AttendanceDayRecord(BaseModel):
    date: date
    check_in: Optional[time]
    check_out: Optional[time]
    work_hours: float
    extra_hours: float
    status: str


class EmployeeMonthAttendance(BaseModel):
    year: int
    month: int
    days_present: float
    leaves_count: int
    total_working_days: int
    records: list[AttendanceDayRecord]


class AdminDayAttendance(BaseModel):
    date: date
    records: list[dict[str, Any]]


class TodayStatusResponse(BaseModel):
    checked_in: bool
    check_in_time: Optional[time]
    status_dot: str  # red or green


# Leave
class LeaveRequestCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    remarks: Optional[str] = None
    attachment_url: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: int
    user_id: int
    employee_name: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    days: float
    remarks: Optional[str]
    status: LeaveStatus
    attachment_url: Optional[str]
    admin_comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveReviewRequest(BaseModel):
    status: LeaveStatus
    admin_comment: Optional[str] = None


class LeaveBalanceResponse(BaseModel):
    paid_time_off: float
    sick_time_off: float


# User
class UserMeResponse(BaseModel):
    id: int
    login_id: str
    email: str
    role: UserRole
    must_change_password: bool
    email_verified: bool
    first_name: Optional[str]
    last_name: Optional[str]
    profile_picture_url: Optional[str]
    company_name: Optional[str]
    company_logo_url: Optional[str]


class CompanyRegisterRequest(BaseModel):
    company_name: str
    logo_url: Optional[str] = None
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    password: str


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    file_url: str
    file_type: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    name: str
    file_url: str
    file_type: Optional[str] = None
