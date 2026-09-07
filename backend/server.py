from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request, HTTPException
from starlette.responses import JSONResponse
from urllib.parse import urlsplit
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import asyncio
from contextlib import suppress
from pathlib import Path
from models.schemas import Health


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
from lib.db import client, db


# Startup runs before the yield, shutdown after it. Add your own setup/teardown here.
@asynccontextmanager
async def lifespan(app: FastAPI):
    from lib.security import ensure_indexes
    await ensure_indexes()
    from lib.recovery import recovery_loop
    recovery = asyncio.create_task(recovery_loop())
    yield
    recovery.cancel()
    with suppress(asyncio.CancelledError):
        await recovery
    client.close()


# Create the main app without a prefix
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


@api_router.get("/", response_model=Health)
@api_router.get('/health', response_model=Health)
async def root():
    return Health()

from routers import (  # noqa: E402
    auth,
    password_reset,
    service,
    google_auth,
    curriculum,
    insights,
    sales_profiles,
    simulations,
    training,
    users,
    voice,
    workspaces,
    evidence,
    privacy,
)

api_router.include_router(auth.router)
api_router.include_router(password_reset.router)
api_router.include_router(service.router)
api_router.include_router(google_auth.router)
api_router.include_router(training.router)
api_router.include_router(users.router)
api_router.include_router(simulations.router)
api_router.include_router(curriculum.router)
api_router.include_router(sales_profiles.router)
api_router.include_router(voice.router)
api_router.include_router(insights.router)
api_router.include_router(workspaces.router)
api_router.include_router(evidence.router)
api_router.include_router(privacy.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[x.strip() for x in os.environ.get('CORS_ORIGINS', '').split(',') if x.strip() and x.strip() != '*'],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.middleware('http')
async def request_origin_guard(request: Request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        allowed = [x.strip() for x in os.environ.get('CORS_ORIGINS', '').split(',') if x.strip() != '*']
        # Same-origin proxy requests plus explicitly configured cross origins only.
        same_origin = bool(origin and urlsplit(origin).netloc == request.headers.get('host'))
        if origin and not same_origin and origin not in allowed:
            return JSONResponse({'detail': 'Request origin is not allowed'}, status_code=403)
        if request.cookies.get('repforge_session') and not origin and not request.headers.get('authorization'):
            return JSONResponse({'detail': 'Origin required for cookie-authenticated changes'}, status_code=403)
    # Normal API requests coexist, while erasure takes an exclusive account gate.
    # Resolve the token without current_user's workspace side effects.
    from lib.auth import session_actor
    from lib.data_guard import data_operation
    actor = await session_actor(request.cookies.get('repforge_session'), request.headers.get('authorization'))
    destructive = request.method == 'DELETE' and request.url.path.startswith('/api/data/')
    try:
        if actor and request.url.path.startswith('/api/') and not destructive:
            async with data_operation(actor['id']):
                response = await call_next(request)
        else:
            response = await call_next(request)
    except HTTPException as exc:
        response = JSONResponse({'detail': exc.detail}, status_code=exc.status_code)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


app.include_router(api_router)
