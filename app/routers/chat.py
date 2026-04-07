from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth_deps import get_current_user, authenticate_user
from app.auth import create_access_token, Token
from app.schemas import BriefRequest, BriefResponse
from app.agent import run_agent

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "department": user["department"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/brief", response_model=BriefResponse)
def generate_brief(payload: BriefRequest, current_user: dict = Depends(get_current_user)):
    # Normalize role to lowercase to match Qdrant RBAC filters and router layer
    user_role = current_user.get("role", "employee").lower()
    username = current_user.get("username", "unknown")
    result = run_agent(payload.query, payload.thread_id, user_role, username)
    return BriefResponse(**result)
