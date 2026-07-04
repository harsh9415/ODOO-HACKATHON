from __future__ import annotations

import enum
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    employee = "employee"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    half_day = "half-day"
    leave = "leave"


class LeaveType(str, enum.Enum):
    paid = "Paid Time Off"
    sick = "Sick Leave"
    unpaid = "Unpaid Leaves"


class LeaveStatus(str, enum.Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    employees: Mapped[list["EmployeeProfile"]] = relationship(back_populates="company")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.employee)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["EmployeeProfile | None"] = relationship(back_populates="user", uselist=False, foreign_keys="EmployeeProfile.user_id")
    bank_details: Mapped["BankDetails | None"] = relationship(back_populates="user", uselist=False)
    resume_info: Mapped["ResumeInfo | None"] = relationship(back_populates="user", uselist=False)
    salary_structure: Mapped["SalaryStructure | None"] = relationship(back_populates="user", uselist=False)
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="user")
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        back_populates="user", foreign_keys="LeaveRequest.user_id"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="user")


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_joining: Mapped[date] = mapped_column(Date, nullable=False)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500))
    dob: Mapped[Optional[date]] = mapped_column(Date)
    residing_address: Mapped[Optional[str]] = mapped_column(Text)
    nationality: Mapped[Optional[str]] = mapped_column(String(100))
    personal_email: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    marital_status: Mapped[Optional[str]] = mapped_column(String(20))
    emp_code: Mapped[Optional[str]] = mapped_column(String(50))

    user: Mapped["User"] = relationship(back_populates="profile", foreign_keys=[user_id])
    company: Mapped["Company"] = relationship(back_populates="employees")
    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id])


class BankDetails(Base):
    __tablename__ = "bank_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(50))
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(20))
    pan_no: Mapped[Optional[str]] = mapped_column(String(20))
    uan_no: Mapped[Optional[str]] = mapped_column(String(20))

    user: Mapped["User"] = relationship(back_populates="bank_details")


class ResumeInfo(Base):
    __tablename__ = "resume_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    about: Mapped[Optional[str]] = mapped_column(Text)
    job_love_note: Mapped[Optional[str]] = mapped_column(Text)
    interests: Mapped[Optional[str]] = mapped_column(Text)
    skills: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    certifications: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship(back_populates="resume_info")


class SalaryStructure(Base):
    __tablename__ = "salary_structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    month_wage: Mapped[float] = mapped_column(Float, default=0)
    working_days_per_week: Mapped[int] = mapped_column(Integer, default=5)
    break_time_minutes: Mapped[int] = mapped_column(Integer, default=60)
    basic_pct: Mapped[float] = mapped_column(Float, default=50.0)
    hra_pct: Mapped[float] = mapped_column(Float, default=50.0)
    standard_allowance_pct: Mapped[float] = mapped_column(Float, default=8.33)
    performance_bonus_pct: Mapped[float] = mapped_column(Float, default=8.33)
    lta_pct: Mapped[float] = mapped_column(Float, default=8.33)
    pf_employee_pct: Mapped[float] = mapped_column(Float, default=12.0)
    pf_employer_pct: Mapped[float] = mapped_column(Float, default=12.0)
    professional_tax: Mapped[float] = mapped_column(Float, default=200.0)

    user: Mapped["User"] = relationship(back_populates="salary_structure")


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_in: Mapped[Optional[time]] = mapped_column(Time)
    check_out: Mapped[Optional[time]] = mapped_column(Time)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, values_callable=lambda x: [e.value for e in x]), default=AttendanceStatus.absent
    )

    user: Mapped["User"] = relationship(back_populates="attendance_records")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus, values_callable=lambda x: [e.value for e in x]), default=LeaveStatus.pending
    )
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    admin_comment: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="leave_requests", foreign_keys=[user_id])
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="documents")
