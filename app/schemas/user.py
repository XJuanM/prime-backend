from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.domain.enums.user_role import Roles


class UserResponse(BaseModel):
    """
    Información pública de un usuario.

    No incluye password_hash ni otros datos privados.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime