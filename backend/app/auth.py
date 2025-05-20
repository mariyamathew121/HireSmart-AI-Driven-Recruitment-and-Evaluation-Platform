from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from .database import users_collection
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta,timezone

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "a1f3e83b0e97f44f6f27c8b1f8de4cc9e64c7289f69a3dc5b9bfa7e7e0a6d3f2"
ALGORITHM = "HS256"

class User(BaseModel):
 email: str
 password: str

@router.post("/login")
async def login(user: User):
 db_user = await users_collection.find_one({"email": user.email})
 print(user.password)
 print(db_user['password'])
 if not db_user or not user.password == db_user["password"]:
  raise HTTPException(status_code=401, detail="Invalid credentials")
#  payload = {
#     "user_id": str(db_user["_id"]),
#  }
#  print(payload) 
#  token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#  print(token)
    
 return {"user_id": str(db_user["_id"])}
   
@router.post("/signup")
async def signup(user_data: User):
    email = user_data.email
    password = pwd_context.hash(user_data.password)

    # Check if user already exists (use await)
    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Insert user into MongoDB
    user_data = {
        "email": email,
        "password": password
    }
    result = await users_collection.insert_one(user_data)

    if result.inserted_id:
        return {"message": "User created successfully"}
    else:
        raise HTTPException(status_code=500, detail="Error creating user")
