"""FastAPI application main module."""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api import auth_router, vehicles_router, commands_router
from .services.rivian_client import rivian_service


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Web interface for Rivian vehicles",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="frontend/templates")

# Include API routers
app.include_router(auth_router)
app.include_router(vehicles_router)
app.include_router(commands_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the index page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.APP_NAME}
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    await rivian_service.close()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )