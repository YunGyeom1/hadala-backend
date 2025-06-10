from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.users.user import crud, schemas
from app.core.auth.utils import get_current_user

router = APIRouter(prefix="/users/user", tags=["user"])

@router.get("/me", response_model=schemas.UserResponse)
def get_my_info(current_user = Depends(get_current_user)):
    return schemas.UserResponse.model_validate(current_user)


@router.put("/me", response_model=schemas.UserResponse)
def update_my_info(
    update_data: schemas.UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.update_user(db=db, user_id=current_user.id, update_data=update_data)
