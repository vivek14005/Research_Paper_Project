from fastapi import UploadFile
from app.repositories.paper import PaperRepository
from app.models.paper import PaperCreate, PaperChunk
from app.rag.pdf_processor import PDFProcessor
from app.rag.vector_store import vector_manager
import os
import aiofiles
from typing import List

class PaperService:
    def __init__(self, paper_repo: PaperRepository):
        self.paper_repo = paper_repo
        self.upload_dir = "uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def process_pdf(self, file: UploadFile, user_id: str):
        file_path = os.path.join(self.upload_dir, f"{user_id}_{file.filename}")
        
        # Save file locally
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Create entry in DB
        paper_create = PaperCreate(
            title=file.filename, # Placeholder, will update from metadata
            authors=[],
            user_id=user_id,
            filename=file.filename,
            file_path=file_path
        )
        paper = await self.paper_repo.create(paper_create)

        try:
            # Extract text and metadata
            processor = PDFProcessor(file_path)
            metadata = processor.extract_metadata()
            pages = processor.get_text_by_page()
            
            # Chunking
            chunks_data = processor.chunk_text(pages)
            paper_chunks = [
                PaperChunk(
                    id=c["id"],
                    paper_id=paper.id,
                    content=c["content"],
                    page_number=c["page_number"],
                    metadata=c["metadata"]
                ) for c in chunks_data
            ]

            # Vector Indexing
            vector_manager.ensure_collection()
            await vector_manager.add_paper_chunks(paper_chunks)

            # Update Paper metadata and status
            await self.paper_repo.update_status(paper.id, "completed")
            # In a real app, we'd update title/authors here too
            
            processor.close()
            return paper

        except Exception as e:
            await self.paper_repo.update_status(paper.id, "error")
            raise e
