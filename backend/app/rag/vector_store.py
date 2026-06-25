from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from app.config import settings
from app.models.paper import PaperChunk
from typing import List
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = "papers"

    def ensure_collection(self):
        from qdrant_client.http import models
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536, # OpenAI embedding size
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

    async def add_paper_chunks(self, chunks: List[PaperChunk]):
        texts = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "paper_id": chunk.paper_id,
                "page_number": chunk.page_number,
                **chunk.metadata
            } for chunk in chunks
        ]
        ids = [chunk.id for chunk in chunks]
        
        vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
        
        vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        logger.info(f"Added {len(chunks)} chunks to Qdrant")

    def get_retriever(self, paper_ids: List[str] = None):
        vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
        
        search_kwargs = {"k": 8}
        if paper_ids:
            from qdrant_client.http import models
            search_kwargs["filter"] = models.Filter(
                must=[
                    models.FieldCondition(
                        key="paper_id",
                        match=models.MatchAny(any=paper_ids)
                    )
                ]
            )
            
        return vector_store.as_retriever(search_kwargs=search_kwargs)

vector_manager = VectorStoreManager()
