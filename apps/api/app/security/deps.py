from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from .jwt import decode_token

bearer = HTTPBearer(auto_error=False)

def require_user(required_scopes: list[str] | None = None):
    def _dep(
        creds: HTTPAuthorizationCredentials = Depends(bearer),
        db: Session = Depends(get_db),
    ) -> User:
        if not creds:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        try:
            payload = decode_token(creds.credentials)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_id = int(payload["sub"])
        token_scopes = payload.get("scopes", [])
        user = db.get(User, user_id)
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="User not found or inactive")

        if required_scopes:
            missing = [s for s in required_scopes if s not in token_scopes]
            if missing:
                raise HTTPException(status_code=403, detail=f"Missing scopes: {missing}")
        return user
    return _dep