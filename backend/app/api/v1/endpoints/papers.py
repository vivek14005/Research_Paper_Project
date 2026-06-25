from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.api import deps
from app.models.user import User
from app.models.paper import Paper, PaperInDB
from app.services.paper import PaperService
from app.repositories.paper import PaperRepository
from app.database.mongodb import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Any

router = APIRouter()

async def get_paper_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> PaperRepository:
    return PaperRepository(db)

async def get_paper_service(paper_repo: PaperRepository = Depends(get_paper_repository)) -> PaperService:
    return PaperService(paper_repo)

@router.post("/upload", response_model=Paper)
async def upload_paper(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
    paper_service: PaperService = Depends(get_paper_service)
) -> Any:
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        paper = await paper_service.process_pdf(file, current_user.id)
        return paper
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Paper])
async def list_papers(
    current_user: User = Depends(deps.get_current_user),
    paper_repo: PaperRepository = Depends(get_paper_repository),
    skip: int = 0,
    limit: int = 100
) -> Any:
    papers = await paper_repo.get_multi_by_user(current_user.id, skip=skip, limit=limit)
    return papers

@router.get("/{paper_id}", response_model=Paper)
async def get_paper(
    paper_id: str,
    current_user: User = Depends(deps.get_current_user),
    paper_repo: PaperRepository = Depends(get_paper_repository)
) -> Any:
    paper = await paper_repo.get_by_id(paper_id)
    if not paper or paper.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper
