
from sqlalchemy import Column, Integer, Boolean, String
from core.settings import DBBaseModel

class UserModel(DBBaseModel):
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String, nullable=False)
    surname: str = Column(String, nullable=False)
    #username: str = Column(String, unique=True, nullable=False)
    email: str = Column(String, unique=True, nullable=False)
    password: str = Column(String, nullable=False)
    is_admin: bool = Column(Boolean, nullable=False, default=False)
    is_active: bool = Column(Boolean, nullable=False, default=True)
