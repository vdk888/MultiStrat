from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
import os
from datetime import datetime

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies core system components are working
    """
    # Basic connectivity check
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check environment variables
    env_vars = {
        "ALPACA_API_KEY": "configured" if os.getenv("ALPACA_API_KEY") else "missing",
        "ALPACA_SECRET_KEY": "configured" if os.getenv("ALPACA_SECRET_KEY") else "missing",
        "ALPACA_BASE_URL": os.getenv("ALPACA_BASE_URL", "missing"),
        "DATABASE_URL": "configured" if os.getenv("DATABASE_URL") else "using default"
    }
    
    return {
        "status": "ok" if db_status == "ok" else "error",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "components": {
            "database": db_status,
            "environment": env_vars
        }
    }
