import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.core.scheduler import setup_scheduler
from app.database.session import engine, Base
from app.routers import register_routers
from app.core.config import get_settings

# Initialize FastAPI app
app = FastAPI(title="Portfolio Management System", 
              description="Multi-Strategy Portfolio Management System",
              version="0.1.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Create database tables
Base.metadata.create_all(bind=engine)

# Register all API routers
register_routers(app)

# Set up scheduler
scheduler = setup_scheduler()

# Home route
@app.get("/")
async def home(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request, "title": "Dashboard"})

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup: start the scheduler"""
    scheduler.start()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown: shutdown the scheduler"""
    scheduler.shutdown()

if __name__ == "__main__":
    # Run the application using Uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
