from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 모든 모델을 임포트하여 Base에 등록
from app.profile.models import *  # noqa
from app.company.common.models import *  # noqa
from app.company.wholesale.models import *  # noqa