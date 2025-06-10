from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 모든 모델을 임포트하여 Base에 등록
from app.users.user.models import *  # noqa
from app.wholesale_company.company.models import *  # noqa
from app.users.farmer.models import *  # noqa
from app.wholesale_company.center.models import *  # noqa
from app.users.wholesaler.models import *  # noqa
from app.users.retailer.models import *  # noqa
from app.transactions.retail_contract.models import *  # noqa
from app.transactions.retail_shipment.models import *  # noqa
from app.transactions.wholesale_contract.models import *  # noqa
from app.transactions.wholesale_shipment.models import *  # noqa
from app.wholesale_company.inventory.models import *  # noqa
from app.wholesale_company.management.models import *  # noqa 