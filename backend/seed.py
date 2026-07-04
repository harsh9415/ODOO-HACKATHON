from __future__ import annotations

"""Seed the database with demo data."""

import asyncio
import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import async_session
from app.models import (
    Attendance,
    AttendanceStatus,
    BankDetails,
    Company,
    EmployeeProfile,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    ResumeInfo,
    SalaryStructure,
    User,
    UserRole,
)
from app.services.login_id_generator import build_login_id


ADMIN_PASSWORD = "Admin@123"
EMPLOYEE_PASSWORD = "Employee@123"


async def seed():
    async with async_session() as db:
        existing = await db.execute(select(Company))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        company = Company(name="Odoo India", logo_url=None)
        db.add(company)
        await db.flush()

        admin = User(
            login_id="OIADMIN20220001",
            email="admin@odooindia.com",
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            role=UserRole.admin,
            must_change_password=False,
            email_verified=True,
        )
        db.add(admin)
        await db.flush()

        admin_profile = EmployeeProfile(
            user_id=admin.id,
            company_id=company.id,
            first_name="Rajesh",
            last_name="Kumar",
            phone="+91 9876543210",
            department="Human Resources",
            location="Bangalore",
            date_of_joining=date(2022, 1, 15),
            dob=date(1985, 3, 20),
            nationality="Indian",
            gender="Male",
            marital_status="Married",
        )
        db.add(admin_profile)
        db.add(ResumeInfo(user_id=admin.id, skills=["HR Management", "Leadership"], certifications=["SHRM-CP"]))
        db.add(BankDetails(user_id=admin.id, account_number="1234567890", bank_name="HDFC Bank", ifsc_code="HDFC0001234"))
        db.add(SalaryStructure(user_id=admin.id, month_wage=80000))

        employees_data = [
            ("John", "Dodo", "john.dodo@odooindia.com", "Engineering", date(2022, 3, 1)),
            ("Priya", "Sharma", "priya.sharma@odooindia.com", "Engineering", date(2022, 6, 15)),
            ("Amit", "Patel", "amit.patel@odooindia.com", "Sales", date(2023, 1, 10)),
            ("Sneha", "Reddy", "sneha.reddy@odooindia.com", "Marketing", date(2023, 8, 20)),
            ("Vikram", "Singh", "vikram.singh@odooindia.com", "Finance", date(2024, 2, 1)),
        ]

        year_counters: dict[int, int] = {}
        created_users = []

        for first, last, email, dept, doj in employees_data:
            year = doj.year
            year_counters[year] = year_counters.get(year, 0) + 1
            login_id = build_login_id(first, last, company.name, year, year_counters[year])

            user = User(
                login_id=login_id,
                email=email,
                hashed_password=get_password_hash(EMPLOYEE_PASSWORD),
                role=UserRole.employee,
                must_change_password=False,
                email_verified=True,
            )
            db.add(user)
            await db.flush()

            profile = EmployeeProfile(
                user_id=user.id,
                company_id=company.id,
                first_name=first,
                last_name=last,
                phone=f"+91 98{random.randint(10000000, 99999999)}",
                department=dept,
                manager_id=admin.id,
                location="Bangalore",
                date_of_joining=doj,
                dob=date(1990 + random.randint(0, 10), random.randint(1, 12), random.randint(1, 28)),
                nationality="Indian",
                gender=random.choice(["Male", "Female"]),
                marital_status=random.choice(["Single", "Married"]),
            )
            db.add(profile)
            db.add(ResumeInfo(user_id=user.id, about=f"Passionate {dept} professional.", skills=["Python", "Communication"]))
            db.add(BankDetails(user_id=user.id))
            db.add(SalaryStructure(user_id=user.id, month_wage=50000))
            created_users.append(user)
            await db.flush()

        today = date.today()
        for user in created_users:
            for days_ago in range(30):
                d = today - timedelta(days=days_ago)
                if d.weekday() >= 5:
                    continue
                if random.random() < 0.15:
                    continue
                check_in = time(9, random.randint(0, 30))
                check_out = time(18, random.randint(0, 30))
                att = Attendance(
                    user_id=user.id,
                    date=d,
                    check_in=check_in,
                    check_out=check_out,
                    status=AttendanceStatus.present,
                )
                db.add(att)

        emp1 = created_users[0]
        leave1 = LeaveRequest(
            user_id=emp1.id,
            leave_type=LeaveType.paid,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=7),
            remarks="Family vacation",
            status=LeaveStatus.pending,
        )
        db.add(leave1)

        leave2 = LeaveRequest(
            user_id=created_users[1].id,
            leave_type=LeaveType.sick,
            start_date=today - timedelta(days=10),
            end_date=today - timedelta(days=10),
            remarks="Medical appointment",
            status=LeaveStatus.approved,
            reviewed_by=admin.id,
        )
        db.add(leave2)

        leave3 = LeaveRequest(
            user_id=created_users[2].id,
            leave_type=LeaveType.paid,
            start_date=today - timedelta(days=3),
            end_date=today - timedelta(days=1),
            remarks="Personal work",
            status=LeaveStatus.rejected,
            admin_comment="Peak sales period",
            reviewed_by=admin.id,
        )
        db.add(leave3)

        if today.weekday() < 5:
            att_today = Attendance(
                user_id=emp1.id,
                date=today,
                check_in=time(9, 15),
                status=AttendanceStatus.present,
            )
            db.add(att_today)

        await db.commit()
        print("Seed complete!")
        print(f"Admin login: OIADMIN20220001 / {ADMIN_PASSWORD}")
        print(f"Employee login: {created_users[0].login_id} / {EMPLOYEE_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
