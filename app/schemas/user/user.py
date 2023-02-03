from pydantic import BaseModel
from typing import List


class ProfileImageSchema(BaseModel):
    profile_picture: str

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    
    full_name: str
    email: str
    password: str
    phone: str
    user_image: List[ProfileImageSchema]
    
    class Config:
        orm_mode = True

