from fastapi import APIRouter, Depends, Query, Response, HTTPException
from lib.auth import current_user, clear_session
from lib.db import db
from lib.privacy import selectors, export_data, delete_account, delete_simulation
from models.privacy import DataSummary, DataExport, DeletionResult

router = APIRouter(prefix='/data', tags=['privacy'])


@router.get('/summary', response_model=DataSummary)
async def summary(me: dict = Depends(current_user)):
    queries = await selectors(me)
    names = ('simulations', 'sales_profiles', 'custom_scenarios')
    return DataSummary(is_guest=bool(me.get('is_guest')), counts={name: await db[name].count_documents(queries[name]) for name in names},
        retention='Training records remain until you delete them. Guests are stored on the server too; signing out or closing a tab does not erase them.')


@router.get('/export', response_model=DataExport)
async def export(response: Response, me: dict = Depends(current_user)):
    response.headers['Content-Disposition'] = 'attachment; filename="repforge-data.json"'
    return await export_data(me)


@router.delete('/account', response_model=DeletionResult)
async def account(response: Response, confirm: str = Query(default=''), me: dict = Depends(current_user)):
    if me.get('is_guest'):
        raise HTTPException(403, 'Use Clear guest data for a guest session.')
    if confirm != 'DELETE':
        raise HTTPException(422, 'Type DELETE to confirm permanent account deletion.')
    result = await delete_account(me)
    clear_session(response)
    return result


@router.delete('/guest', response_model=DeletionResult)
async def guest(response: Response, confirm: str = Query(default=''), me: dict = Depends(current_user)):
    if not me.get('is_guest'):
        raise HTTPException(403, 'This control is only for the current guest.')
    if confirm != 'DELETE':
        raise HTTPException(422, 'Type DELETE to confirm clearing this guest’s data.')
    result = await delete_account(me, 'guest')
    clear_session(response)
    return result


@router.delete('/sessions/{sim_id}', response_model=DeletionResult)
async def session(sim_id: str, confirm: str = Query(default=''), me: dict = Depends(current_user)):
    if confirm != 'DELETE':
        raise HTTPException(422, 'Type DELETE to confirm permanent session deletion.')
    return await delete_simulation(me, sim_id)