"""Public contact settings and low-information readiness for uptime checks."""
import asyncio
import os
from fastapi import APIRouter
from starlette.responses import JSONResponse
from lib.db import db
from lib.mail import recovery_configured

router = APIRouter(tags=['service'])


@router.get('/site-info')
async def site_info():
    return {'operator': os.environ.get('PUBLIC_OPERATOR_NAME', ''),
            'support_email': os.environ.get('PUBLIC_SUPPORT_EMAIL', ''),
            'privacy_email': os.environ.get('PUBLIC_PRIVACY_EMAIL', ''),
            'password_recovery': recovery_configured()}


@router.get('/ready')
async def readiness():
    try:
        await asyncio.wait_for(db.command('ping'), timeout=2)
        return JSONResponse({'status': 'ready'}, headers={'Cache-Control': 'no-store'})
    except Exception:
        return JSONResponse({'status': 'unavailable'}, status_code=503, headers={'Cache-Control': 'no-store'})
