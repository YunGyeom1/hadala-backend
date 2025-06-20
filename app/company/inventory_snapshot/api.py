from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.company.inventory_snapshot.schemas import (
    DailyInventorySnapshot,
    UpdateDailyInventorySnapshotRequest,
    CenterInventorySnapshot
)
from app.company.inventory_snapshot.crud import (
    get_daily_company_inventory_snapshot,
    get_daily_company_inventory_snapshots_by_date_range,
    get_daily_center_inventory_snapshot,
    create_daily_center_inventory_snapshot,
    update_daily_inventory_snapshot
)
from app.database import get_db
from app.core.auth.dependencies import get_current_user
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile
from uuid import UUID

router = APIRouter(prefix="/inventory-snapshots", tags=["inventory-snapshots"])

@router.get("/company/{company_id}/date/{target_date}", response_model=DailyInventorySnapshot)
def get_company_inventory_snapshot(
    company_id: UUID,
    target_date: date,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    특정 날짜의 회사 전체 인벤토리 스냅샷을 조회합니다.
    """
    result = get_daily_company_inventory_snapshot(db, target_date, company_id)
    if not result or not result.centers:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="회사 인벤토리 스냅샷을 찾을 수 없습니다.")
    return result

@router.get("/company/{company_id}/date-range", response_model=List[DailyInventorySnapshot])
def get_company_inventory_snapshots_by_date_range(
    company_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    특정 기간의 회사 전체 인벤토리 스냅샷 목록을 조회합니다.
    """
    result = get_daily_company_inventory_snapshots_by_date_range(db, start_date, end_date, company_id)
    return result or []

@router.get("/center/{center_id}/date/{target_date}", response_model=CenterInventorySnapshot)
def get_center_inventory_snapshot(
    center_id: UUID,
    target_date: date,
    company_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    특정 날짜의 센터 인벤토리 스냅샷을 조회합니다.
    """
    result = get_daily_center_inventory_snapshot(db, target_date, company_id, center_id)
    if not result:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="센터 인벤토리 스냅샷을 찾을 수 없습니다.")
    return result

@router.post("/center/{center_id}/date/{target_date}", response_model=CenterInventorySnapshot)
def create_center_inventory_snapshot(
    center_id: UUID,
    target_date: date,
    company_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    current_profile: Profile = Depends(get_current_profile)
):
    """
    특정 날짜의 센터 인벤토리 스냅샷을 생성합니다.
    전날 데이터와 오늘 출하 데이터를 합산하여 생성합니다.
    """
    return create_daily_center_inventory_snapshot(db, target_date, company_id, center_id, current_profile.id)

@router.put("/company/{company_id}/date/{target_date}", response_model=DailyInventorySnapshot)
def update_company_inventory_snapshot(
    company_id: UUID,
    target_date: date,
    update_request: UpdateDailyInventorySnapshotRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    current_profile: Profile = Depends(get_current_profile),
    contract_id: UUID = Query(None)
):
    """
    특정 날짜의 회사 전체 인벤토리 스냅샷을 수정합니다.
    수정된 데이터는 이후 날짜의 스냅샷에도 반영됩니다.
    """
    updated_snapshot, _, _ = update_daily_inventory_snapshot(
        db=db,
        update_request=update_request,
        company_id=company_id,
        profile_id=current_profile.id,
        contract_id=contract_id
    )
    return updated_snapshot 