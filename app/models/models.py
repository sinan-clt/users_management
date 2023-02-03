from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

    
class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    full_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    phone = Column(String, unique=True)

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(String, primary_key=True)
    profile_picture = Column(String)
    user_id = Column(String, ForeignKey('users.id'))
    user = relationship("User", backref='user_image')
    