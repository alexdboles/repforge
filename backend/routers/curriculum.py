from fastapi import APIRouter, HTTPException

from lib.curriculum import MODULES, module_for
from models.schemas import TrainingModule

router = APIRouter(tags=["curriculum"])


@router.get("/curriculum", response_model=list[TrainingModule])
async def list_modules():
    return list(MODULES.values())


@router.get("/curriculum/{exercise_id}", response_model=TrainingModule)
async def get_module(exercise_id: str):
    mod = module_for(exercise_id)
    if not mod:
        raise HTTPException(status_code=404, detail="No training module for this exercise")
    return mod
