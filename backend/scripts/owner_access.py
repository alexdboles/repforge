"""Private operator-only promotion of a verified existing account; no passwords accepted.
Creates a 0600 BSON pre-change record for recovery. Not imported by the API.
"""
import asyncio
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bson import BSON
from lib.db import db


async def main(uid):
    user = await db.users.find_one({'id': uid, 'is_guest': {'$ne': True}})
    if not user:
        raise SystemExit('Existing non-guest account required')
    folder = (Path(__file__).resolve().parents[2] / 'checkpoints')
    folder.mkdir(mode=0o700, exist_ok=True)
    path = folder / f'owner-before-{uid}.bson'
    if not path.exists():
        with path.open('xb') as out:
            os.chmod(path, 0o600)
            out.write(BSON.encode(user))
    await db.users.update_one({'id': uid}, {'$set': {'is_admin': True}})
    print('Owner access granted to the specified account; sign in again to refresh.')


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1]))