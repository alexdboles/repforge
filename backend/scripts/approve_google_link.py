"""PRIVATE OPERATOR ACTION: use only after explicit account-owner approval.

No public approval endpoint. Never infer approval from matching email alone.
--pending-approved selects exactly ONE non-fixture pending Google identity; otherwise
require the user's non-secret recovery reference. Original records are backed up.
Never prints emails, hashes, tokens, state/verifiers or passwords.
"""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bson import BSON
from lib.db import db
from lib.google_auth import _bind
from lib.security import digest, lease
from models.google_auth import ManagedGoogleIdentity


async def approve(reference: str):
    now = datetime.now(timezone.utc)
    if reference == '--pending-approved':
        candidates = []
        async for flow in db.oauth_flows.find({'status': 'link_required', 'expires_at': {'$gt': now}, 'identity': {'$exists': True}}):
            email = flow['identity'].get('email', '').lower()
            if email.endswith(('@example.com', '@example.test', '@repforge.test')):
                continue
            candidates.append(flow)
        if len(candidates) != 1:
            raise SystemExit('No unique current non-fixture pending identity. Ask the owner to retry Google sign-in or supply their recovery reference; do not guess.')
        record = candidates[0]
    else:
        record = await db.oauth_recoveries.find_one({'_id': reference, 'status': 'pending', 'expires_at': {'$gt': now}})
        if not record:
            raise SystemExit('No active recovery request matches that reference.')
    identity = ManagedGoogleIdentity.model_validate(record['identity'])
    if identity.email_verified is False:
        raise SystemExit('Provider explicitly rejected email verification; do not approve.')
    email = str(identity.email).lower()
    user = await db.users.find_one({'email': email})
    if not user or user.get('is_guest'):
        raise SystemExit('No matching permanent account. No changes made.')
    uid = user['id']
    target_id = record.get('user_id') or record.get('link_user_id')
    if target_id and target_id != uid:
        raise SystemExit('The account associated with this request changed. No changes made.')
    folder = Path('/app/checkpoints') / ('google-link-approved-' + now.strftime('%Y%m%dT%H%M%S%f'))
    folder.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest = {}
    selectors = {'users': {'id': uid}, 'memberships': {'user_id': uid},
                 'simulations': {'user_id': uid}, 'oauth_identities': {'user_id': uid}}
    for name, selector in selectors.items():
        path = folder / (name + '.bson')
        count = 0
        with path.open('xb') as stream:
            os.chmod(path, 0o600)
            async for doc in db[name].find(selector):
                stream.write(BSON.encode(doc)); count += 1
        manifest[name] = {'count': count, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    with (folder / 'manifest.json').open('x') as stream:
        os.chmod(folder / 'manifest.json', 0o600)
        json.dump(manifest, stream)
    before_user = BSON.encode(user)
    before_memberships = [BSON.encode(x) async for x in db.memberships.find({'user_id': uid}).sort('_id', 1)]
    before_turns = {x['id']: BSON.encode({'transcript': x.get('transcript', [])}) async for x in db.simulations.find({'user_id': uid})}
    async with lease('google-account:' + digest(email), 30):
        await _bind(identity, uid)
        await db.oauth_identities.update_one({'user_id': uid}, {'$set': {
            'link_method': 'explicit-account-owner-approval', 'approved_at': now}})
    if reference != '--pending-approved':
        await db.oauth_recoveries.update_one({'_id': reference}, {'$set': {'status': 'approved', 'approved_at': now}})
    assert before_user == BSON.encode(await db.users.find_one({'id': uid})), 'Unexpected account-field change; inspect private checkpoint'
    assert before_memberships == [BSON.encode(x) async for x in db.memberships.find({'user_id': uid}).sort('_id', 1)], 'Unexpected membership change'
    after_turns = {x['id']: BSON.encode({'transcript': x.get('transcript', [])}) async for x in db.simulations.find({'user_id': uid})}
    assert all(after_turns.get(k) == v for k, v in before_turns.items()), 'Unexpected transcript change'
    print(json.dumps({'google_connected': True, 'account_fields_unchanged': True,
        'permissions_unchanged': True, 'existing_transcripts_unchanged': True,
        'private_checksummed_backup_created': True}))


if __name__ == '__main__':
    asyncio.run(approve(sys.argv[1]))