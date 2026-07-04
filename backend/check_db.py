import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import User

async def main():
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Total users found: {len(users)}")
        for u in users:
            print(f"User ID: {u.id}, Login ID: {u.login_id}, Email: {u.email}, Password Hash: {u.hashed_password}, Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(main())
