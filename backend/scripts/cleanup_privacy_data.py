"""Private operator tool. Dry-run by default; no bulk guest deletion or scheduler.

Usage from backend/: python scripts/cleanup_privacy_data.py --guest-id UUID
Execute only an authorised target: add --confirm DELETE
Temporary expiry maintenance: --expired-temporary [--confirm DELETE]
"""
import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.db import db
from lib.privacy import delete_account, selectors


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--guest-id')
    mode.add_argument('--expired-temporary', action='store_true')
    parser.add_argument('--confirm', choices=['DELETE'])
    args = parser.parse_args()
    if args.expired_temporary:
        for name in ('oauth_flows', 'oauth_codes', 'oauth_recoveries', 'audio_cache', 'invitations', 'rate_limits', 'leases'):
            query = {'expires_at': {'$lte': datetime.now(timezone.utc)}}
            count = await db[name].count_documents(query)
            if args.confirm:
                await db[name].delete_many(query)
            print(name, count, 'deleted' if args.confirm else 'would delete')
        return
    user = await db.users.find_one({'id': args.guest_id, 'is_guest': True})
    if not user:
        raise SystemExit('Guest not found. Registered accounts are never targeted by this tool.')
    if args.confirm:
        result = await delete_account(user, 'guest')
        print(result.model_dump_json())
    else:
        print('DRY RUN. Confirm ownership/authorisation before using --confirm DELETE.')
        for name, query in (await selectors(user)).items():
            print(name, await db[name].count_documents(query))


if __name__ == '__main__':
    asyncio.run(main())