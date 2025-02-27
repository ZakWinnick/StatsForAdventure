from fastapi import APIRouter, Response

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}
