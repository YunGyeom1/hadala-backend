from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from uuid import UUID
from app.database.session import get_db
from app.core.auth.models import User
from app.profile import crud
from sqlalchemy.orm import Session
from app.core.auth.dependencies import get_current_user


async def get_current_profile(
    current_profile_id: Optional[UUID] = Header(None, description="현재 사용 중인 프로필 ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    헤더의 current_profile_id를 통해 현재 사용 중인 프로필을 가져옵니다.
    """
    if not current_profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="current_profile_id 헤더가 필요합니다"
        )
    
    profile = crud.get_profile(db, current_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로필을 찾을 수 없습니다"
        )
    
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 프로필에 대한 접근 권한이 없습니다"
        )
    
    return profile 