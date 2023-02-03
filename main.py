from fastapi import FastAPI, status, File, UploadFile, Form, HTTPException
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import uuid
from app.schemas.user.user import UserBase
from app.models.models import *
from pymongo import MongoClient
from hashlib import sha256


# -------- replace the db_name and password according to your database details --------------
engine = create_engine('postgresql://postgres:password@localhost/users_management')
Session = sessionmaker(bind=engine, autoflush=False,)
Base.metadata.create_all(engine)


app = FastAPI()
Base = declarative_base()


client = MongoClient("mongodb://localhost:27017/")
db = client["users_management"]
collection = db["users"]


@app.post('/register')
async def register(full_name: str = Form(...), email: str = Form(...), password: str = Form(...), phone: str = Form(...), profile_picture: UploadFile = File(...)):
    session = Session()
    existing_user = session.query(User).filter_by(email=email).first()
    existing_phone = session.query(User).filter_by(phone=phone).first()
    if existing_user:
        return JSONResponse(content={"message": "Email already exists"}, status_code=HTTP_400_BAD_REQUEST)
    if existing_phone:
        return JSONResponse(content={"message": "Phone number already exists"}, status_code=HTTP_400_BAD_REQUEST)
    file_path = "images/{}.jpg".format(str(uuid.uuid4()))
    with open(file_path, "wb") as f:
        f.write(await profile_picture.read())
    user_id = str(uuid.uuid4())
    user_db = User(id=user_id, full_name=full_name, email=email, password=password, phone=phone)
    session.add(user_db)
    session.commit()
    profile_db = Profile(id=str(uuid.uuid4()), user_id=user_id, profile_picture=file_path)
    session.add(profile_db)
    session.commit()
    return JSONResponse(content={"message": "User registered successfully"}, status_code=HTTP_201_CREATED)


def get_userdetails_by_id(id: int):
    session = Session()
    return session.query(User).get(id)

        
@app.get("/user/{user_id}", response_model=UserBase, status_code=status.HTTP_200_OK)
async def get_user_details_by_id(user_id: str):
    details = get_userdetails_by_id(user_id)
    return details
        

# -------- Using MongoDB --------

def get_password_hash(password: str):
    return sha256(password.encode()).hexdigest()


def check_email_exists(session, email: str):
    return session.query(User).filter(User.email == email).count() > 0


def save_profile_picture(user_id: int, file: UploadFile):
    collection.update_one({"user_id": user_id}, {"$set": {"profile_picture": file.read()}}, upsert=True)


@app.post("/registerbymongodb")
async def register(full_name: str = Form(...), email: str = Form(...), password: str = Form(...), phone: str = Form(...), profile_picture: UploadFile = File(...)):
    session = Session()
    try:
        if check_email_exists(session, email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        new_user = User(
            full_name=full_name,
            email=email,
            password=get_password_hash(password),
            phone=phone
        )
        session.add(new_user)
        session.commit()

        save_profile_picture(new_user.id, profile_picture)

        return {"message": "User registered successfully"}
    finally:
        session.close()


def get_user_details_postgres(user_id: int):
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return user
        else:
            raise HTTPException(status_code=400, detail="User not found")
    finally:
        session.close()
        

def get_user_details_mongo(user_id: int):
    user = collection.find_one({"user_id": user_id})
    if user:
        return user
    else:
        raise HTTPException(status_code=400, detail="User not found")


@app.get("/getusers/{user_id}")
async def get_user_details(user_id: int):
    user_postgres = get_user_details_postgres(user_id)
    user_mongo = get_user_details_mongo(user_id)
    return {
        "full_name": user_postgres.full_name,
        "email": user_postgres.email,
        "password": user_postgres.password,
        "phone": user_postgres.phone,
        "profile_picture": user_mongo.get("profile_picture", None)
    }