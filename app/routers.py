from fastapi import APIRouter
from app.api.endpoints import health, assets, optimization, portfolios

def register_routers(app):
    """
    Register all API routers with the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    # Create API router
    api_router = APIRouter(prefix="/api/v1")
    
    # Register endpoint routers
    api_router.include_router(health.router, tags=["health"])
    api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
    api_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
    api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
    
    # Include API router in the app
    app.include_router(api_router)
    
    return app
