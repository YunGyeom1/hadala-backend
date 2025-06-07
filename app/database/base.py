from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 모든 모델을 임포트하여 Base에 등록
from app.user.models import *  # noqa
from app.company.models import *  # noqa
from app.farmer.models import *  # noqa
from app.center.models import *  # noqa
from app.wholesaler.models import *  # noqa
from app.retailer.models import *  # noqa
from app.retail_contract.models import *  # noqa
from app.retail_shipment.models import *  # noqa
from app.wholesale_contract.models import *  # noqa
from app.wholesale_shipment.models import *  # noqa
from app.inventory.models import *  # noqa
from app.management.models import *  # noqa 