from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    public_token: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    user_id: Optional[str] = None
