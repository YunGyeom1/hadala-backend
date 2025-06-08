from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.company import crud, schemas
from app.company.utils import check_company_permission
from app.database import get_db
from app.user.models import User
from app.user.api import get_current_user
from app.wholesaler.utils import get_wholesaler
from app.wholesaler.schemas import WholesalerOut
from app.center.schemas import CenterOut
router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=schemas.CompanyOut)
def create_company(
    company: schemas.CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    새로운 회사를 생성합니다.
    도매상 로그인이 필요합니다.
    """
    # 도매상 권한 체크
    wholesaler = get_wholesaler(db, current_user.id)
    
    # 이미 회사를 소유하고 있는지 체크
    if wholesaler.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 회사를 소유하고 있습니다"
        )
    
    # 회사 생성 및 도매상을 소유자로 설정
    db_company = crud.create_company(db=db, company=company, user_id=current_user.id)
    
    # 도매상의 회사 ID와 역할 업데이트
    wholesaler.company_id = db_company.id
    wholesaler.role = 'owner'
    db.commit()
    
    return db_company


@router.get("/", response_model=schemas.CompanyList)
def read_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str = None,
    db: Session = Depends(get_db)
):
    """
    회사 목록을 조회합니다.
    검색어가 있는 경우 이름, 사업자번호, 주소로 검색합니다.
    """
    companies = crud.get_companies(db, skip=skip, limit=limit, search=search)
    total = db.query(crud.models.Company).count()
    
    return {
        "items": companies,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{company_id}", response_model=schemas.CompanyOut)
def read_company(company_id: UUID, db: Session = Depends(get_db)):
    company = crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=schemas.CompanyOut)
def update_company(
    company_id: UUID,
    company_update: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    회사 정보를 수정합니다.
    회사 소유자만 가능합니다.
    """
    check_company_permission(
        db,
        user=current_user,
        company_id=company_id,
        allowed_roles=['owner']
    )
    
    updated_company = crud.update_company(db, company_id, company_update)
    if not updated_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    return updated_company


@router.get("/{company_id}/wholesalers", response_model=List[schemas.WholesalerOut])
def read_company_wholesalers(
    company_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    회사 소속 도매상 목록을 조회합니다.
    해당 회사 소속 도매상만 가능합니다.
    """
    check_company_permission(
        db,
        user=current_user,
        company_id=company_id,
        allowed_roles=['owner', 'manager', 'staff']
    )
    
    wholesalers = crud.get_company_wholesalers(db, company_id, skip=skip, limit=limit)
    for w in wholesalers:
        if w.company_id is None:
            w.company_id = company_id
    return wholesalers


@router.get("/{company_id}/centers", response_model=List[CenterOut])
def read_company_centers(
    company_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    회사 소유 집하장 목록을 조회합니다.
    해당 회사 소속 도매상만 가능합니다.
    """
    check_company_permission(
        db,
        user=current_user,
        company_id=company_id,
        allowed_roles=['owner', 'manager', 'staff']
    )
    
    return crud.get_company_centers(db, company_id, skip=skip, limit=limit)
