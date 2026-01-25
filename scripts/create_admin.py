#!/usr/bin/env python3
"""Script to create an admin user."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import AsyncSessionLocal
from app.models.user import User


async def create_admin(email: str, password: str, name: str = "Admin"):
    """Create an admin user."""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"User with email {email} already exists")
            return

        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            name=name,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"Created admin user: {email}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <email> <password> [name]")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "Admin"

    asyncio.run(create_admin(email, password, name))
