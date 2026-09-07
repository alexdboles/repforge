"""Test-only helper: create a real RepForge password account directly against the
DB (same hashing/workspace code the signup route uses), bypassing the per-IP
signup rate limit that repeated test runs share. Not app code; not imported by it.

Usage: python -m tests.helpers_create_account <email> <name> <password>
"""
import sys
import asyncio
sys.path.insert(0, __file__.rsplit('/backend/', 1)[0] + '/backend')
from lib.db import db
from lib.auth import hash_password, personal_workspace
from models.schemas import UserProfile


async def main():
    email, name, password = sys.argv[1:4]
    email = email.strip().lower()
    existing = await db.users.find_one({'email': email})
    if existing:
        return
    profile = UserProfile(name=name)
    doc = profile.model_dump()
    doc['email'] = email
    doc['password'] = hash_password(password)
    doc['is_guest'] = False
    await db.users.insert_one(doc)
    await personal_workspace(doc)


if __name__ == '__main__':
    asyncio.run(main())
