from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.api import api_router
from app.database.mongodb import db as mongodb_db
from app.database.qdrant import qdrant_db

def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Set all CORS enabled origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.on_event("startup")
    async def startup_event():
        await mongodb_db.connect_to_storage()
        qdrant_db.connect_to_storage()

    @application.on_event("shutdown")
    async def shutdown_event():
        await mongodb_db.close_storage_connection()
        qdrant_db.close_storage_connection()

    @application.get("/")
    async def root():
        return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "mongodb": "connected" if mongodb_db.client else "disconnected",
            "qdrant": "connected" if qdrant_db.client else "disconnected"
        }

    return application

app = get_application()
