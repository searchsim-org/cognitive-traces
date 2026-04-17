from fastapi import APIRouter, Depends

from app.auth.deps import get_current_user
from app.db.models import User
from app.schemas.auth import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
