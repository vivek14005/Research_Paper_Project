import fitz # PyMuPDF
import re
from typing import List, Dict, Any
from app.models.paper import PaperChunk
import uuid

class PDFProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = fitz.open(file_path)

    def extract_metadata(self) -> Dict[str, Any]:
        metadata = self.doc.metadata
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creationDate": metadata.get("creationDate", ""),
            "modDate": metadata.get("modDate", ""),
            "page_count": self.doc.page_count
        }

    def get_text_by_page(self) -> List[Dict[str, Any]]:
        pages = []
        for page_num in range(self.doc.page_count):
            page = self.doc.load_page(page_num)
            text = page.get_text("text")
            pages.append({
                "page_number": page_num + 1,
                "text": text
            })
        return pages

    def chunk_text(self, pages: List[Dict[str, Any]], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        chunks = []
        current_chunk = ""
        current_page_nums = []
        
        for page in pages:
            text = page["text"]
            words = text.split()
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "content": chunk_text,
                    "page_number": page["page_number"],
                    "metadata": {
                        "source": self.file_path,
                        "page": page["page_number"]
                    }
                })
                
        return chunks

    def close(self):
        self.doc.close()

    @staticmethod
    def clean_text(text: str) -> str:
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove hyphenation at end of lines
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
        return text.strip()
