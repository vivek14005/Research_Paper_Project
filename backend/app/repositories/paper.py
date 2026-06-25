from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.paper import PaperCreate, PaperInDB, PaperUpdate
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

class PaperRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["papers"]

    async def create(self, paper_create: PaperCreate) -> PaperInDB:
        paper_dict = paper_create.dict()
        paper_dict["created_at"] = datetime.utcnow()
        paper_dict["updated_at"] = datetime.utcnow()
        paper_dict["status"] = "processing"
        
        result = await self.collection.insert_one(paper_dict)
        paper_dict["_id"] = str(result.inserted_id)
        return PaperInDB(**paper_dict)

    async def get_by_id(self, paper_id: str) -> Optional[PaperInDB]:
        if not ObjectId.is_valid(paper_id):
            return None
        paper_dict = await self.collection.find_one({"_id": ObjectId(paper_id)})
        if paper_dict:
            paper_dict["_id"] = str(paper_dict["_id"])
            return PaperInDB(**paper_dict)
        return None

    async def get_multi_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[PaperInDB]:
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
        papers = []
        async for paper_dict in cursor:
            paper_dict["_id"] = str(paper_dict["_id"])
            papers.append(PaperInDB(**paper_dict))
        return papers

    async def update_status(self, paper_id: str, status: str) -> bool:
        if not ObjectId.is_valid(paper_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(paper_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
