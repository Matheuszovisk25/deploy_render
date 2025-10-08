from typing import Optional

from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    id: Optional[int] = None
    name: str
    surname: str
    email: EmailStr
    #password: str
    is_admin: bool = False
    is_active: bool = True

    model_config = {
        "from_attributes": True
    }


class UserSchemaCreate(UserSchema):
    password: str


class UserSchemaUp(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    #is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = {
        "from_attributes": True
    }


