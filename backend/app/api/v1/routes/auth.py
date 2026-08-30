from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user, get_repositories
from app.models.domain import User
from app.repositories.factory import Repositories
from app.schemas.common import GoogleLogin, TokenPair, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, repos: Repositories = Depends(get_repositories)) -> User:
    try:
        return await AuthService(repos).register(payload.email, payload.full_name, payload.password, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, repos: Repositories = Depends(get_repositories)) -> TokenPair:
    try:
        return await AuthService(repos).login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/google", response_model=TokenPair)
async def google_login(payload: GoogleLogin, repos: Repositories = Depends(get_repositories)) -> TokenPair:
    try:
        return await AuthService(repos).google_login(payload.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
