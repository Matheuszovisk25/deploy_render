from typing import Optional
from pydantic import BaseModel, EmailStr

# ===== Saída (response) =====
class UserOut(BaseModel):
    id: int
    name: str
    surname: Optional[str] = None
    email: EmailStr
    is_active: bool

    model_config = {"from_attributes": True}

# ===== Entrada (create) =====
class UserCreate(BaseModel):
    name: str
    surname: Optional[str] = None
    email: EmailStr
    password: str

# ===== Entrada (update) =====
class UserUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    # is_admin: só mexa em rota exclusiva de admin (opcional)
    # is_admin: Optional[bool] = None

    model_config = {"from_attributes": True}
