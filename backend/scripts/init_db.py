"""
Database initialization script
Creates tables and adds initial admin user
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import async_session_maker, engine, Base
from app.models.user import User
from app.core.security import get_password_hash


async def init_db():
    """Initialize database with tables and default users"""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database tables created")
    
    # Create default users
    async with async_session_maker() as session:
        # Check if admin exists
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("✓ Admin user already exists")
        else:
            admin = User(
                username="admin",
                email="admin@radiomics.local",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                role="admin",
                is_active=True
            )
            session.add(admin)
            print("✓ Admin user created (admin/admin123)")
        
        # Check if doctor exists
        result = await session.execute(select(User).where(User.username == "doctor"))
        if result.scalar_one_or_none():
            print("✓ Doctor user already exists")
        else:
            doctor = User(
                username="doctor",
                email="doctor@radiomics.local",
                hashed_password=get_password_hash("doctor123"),
                full_name="测试医生",
                role="doctor",
                is_active=True
            )
            session.add(doctor)
            print("✓ Doctor user created (doctor/doctor123)")
        
        await session.commit()
    
    print("\n✅ Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())