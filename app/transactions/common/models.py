import enum
from sqlalchemy import Enum

class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PREPARED = "prepared"
    OVERDUE = "overdue"
    PAID = "paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class ShipmentStatus(str, enum.Enum):
    PENDING = "pending"               # 출하 대기 (생성만 되고 아직 시작 안 됨)
    READY = "ready"                   # 운송 준비 완료 (차량/기사 할당 등)
    DELIVERED = "delivered"           # 배송 완료 (수령자 확인 포함)
    FAILED = "failed"                 # 배송 실패 (주소 오류, 부재 등)
    CANCELLED = "cancelled"   

class ProductQuality(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"