from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.wholesaler.models import Wholesaler


def get_wholesaler(db: Session, user_id: UUID) -> Wholesaler:
    """
    사용자 ID로 도매상 정보를 조회합니다.
    존재하지 않으면 403 예외 발생.
    """
    wholesaler = db.query(Wholesaler).filter(Wholesaler.user_id == user_id).first()
    if not wholesaler:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상으로 가입되어 있지 않습니다."
        )
    return wholesaler