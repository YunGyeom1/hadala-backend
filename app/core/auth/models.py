from datetime import datetime
from typing import Optional
import uuid

class Token:
    def __init__(
        self,
        sub: str,
        token_type: str,
        exp: datetime,
        jti: str = None
    ):
        self.sub = sub
        self.token_type = token_type
        self.exp = exp
        self.jti = jti or str(uuid.uuid4())