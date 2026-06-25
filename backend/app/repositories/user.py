from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserCreate, UserUpdate, UserInDB
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        user_dict = await self.collection.find_one({"email": email})
        if user_dict:
            user_dict["_id"] = str(user_dict["_id"])
            return UserInDB(**user_dict)
        return None

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        if not ObjectId.is_valid(user_id):
            return None
        user_dict = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user_dict:
            user_dict["_id"] = str(user_dict["_id"])
            return UserInDB(**user_dict)
        return None

    async def create(self, user_create: UserCreate, hashed_password: str) -> UserInDB:
        user_dict = user_create.dict()
        user_dict["hashed_password"] = hashed_password
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        return UserInDB(**user_dict)

    async def update(self, user_id: str, user_update: UserUpdate) -> Optional[UserInDB]:
        if not ObjectId.is_valid(user_id):
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await self.collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": update_data}
        )
        return await self.get_by_id(user_id)
