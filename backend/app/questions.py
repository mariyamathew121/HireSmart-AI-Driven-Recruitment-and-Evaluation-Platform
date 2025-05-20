from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt
from pymongo import ReturnDocument
# from .database import result_collection  # Ensure this is your MongoDB results collection

router = APIRouter()

# OAuth2 scheme to extract JWT from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Use the same secret and algorithm as in your auth module
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# Dependency to extract the current user's id from the token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not found in token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class ScoreSubmission(BaseModel):
    user_id: str
    score: int

# @router.post("/submit")
# async def submit_score(score_submission: ScoreSubmission):
#     user_id = score_submission.user_id
#     score = score_submission.score

#     # Using find_one_and_update to update (or insert) the document for the user.
#     updated_document = await result_collection.find_one_and_update(
#         {"user_id": user_id},   # Filter: document with matching user_id
#         {"$set": {"test_score": score}},  # Set/insert new field 'test_score'
#         upsert=True,
#         return_document=ReturnDocument.AFTER  # Return the updated document
#     )

#     if not updated_document:
#         raise HTTPException(status_code=500, detail="Unable to update score.")

#     return {"message": "Score saved successfully", "result": updated_document}
