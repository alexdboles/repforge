"""Additive privacy migration with mandatory checksummed BSON backup.
Run: python scripts/safe_migrate.py backup|migrate|restore BACKUP_DIRECTORY
Restore replaces checkpoint records only; never deletes newer user data.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bson import BSON, decode_all
from lib.db import db

COLLECTIONS = ('users', 'assignments', 'simulations', 'memberships', 'workspaces')


async def main(action, directory):
    folder = Path(directory)
    if action == 'backup':
        folder.mkdir(parents=True, exist_ok=False, mode=0o700)
        manifest = {}
        for name in COLLECTIONS:
            path = folder / f'{name}.bson'
            count = 0
            with path.open('wb') as out:
                os.chmod(path, 0o600)
                async for doc in db[name].find({}):
                    out.write(BSON.encode(doc))
                    count += 1
            manifest[name] = {'count': count, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        print(json.dumps({k: v['count'] for k, v in manifest.items()}))
        return
    manifest = json.loads((folder / 'manifest.json').read_text())
    for name, info in manifest.items():
        if hashlib.sha256((folder / f'{name}.bson').read_bytes()).hexdigest() != info['sha256']:
            raise RuntimeError('Backup checksum mismatch')
    if action == 'restore':
        for name in COLLECTIONS:
            for doc in decode_all((folder / f'{name}.bson').read_bytes()):
                await db[name].replace_one({'_id': doc['_id']}, doc, upsert=True)
        print('Checkpoint records restored; newer records not deleted.')
        return
    if action != 'migrate':
        raise ValueError('Unknown action')
    seen = set()
    async for user in db.users.find({'email': {'$type': 'string'}}):
        email = user['email'].strip().lower()
        if email in seen:
            raise RuntimeError('Duplicate normalized emails need operator resolution; no migration applied')
        seen.add(email)
    count = 0
    async for user in db.users.find({}):
        uid = user['id']
        wid = str(uuid.uuid5(uuid.NAMESPACE_URL, f'repforge:personal:{uid}'))
        await db.workspaces.update_one({'id': wid}, {'$setOnInsert': {
            'id': wid, 'name': user.get('org') or 'Personal', 'kind': 'personal', 'owner_id': uid,
        }}, upsert=True)
        await db.memberships.update_one({'workspace_id': wid, 'user_id': uid}, {'$setOnInsert': {
            'workspace_id': wid, 'user_id': uid, 'role': 'owner', 'verified': True,
            'source': 'isolated-personal-migration',
        }}, upsert=True)
        updates = {'personal_workspace_id': wid}
        if not user.get('workspace_id'):
            updates['workspace_id'] = wid
        if user.get('email'):
            updates['email'] = user['email'].strip().lower()
        await db.users.update_one({'id': uid}, {'$set': updates})
        count += 1
    await db.assignments.update_many({'workspace_id': {'$exists': False}}, {'$set': {'membership_unverified': True}})
    await db.users.create_index('email', unique=True, partialFilterExpression={'email': {'$type': 'string'}})
    print(f'Migrated {count} isolated personal memberships; historical records preserved.')


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1], sys.argv[2]))