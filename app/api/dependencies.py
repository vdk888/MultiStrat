from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
import os
from app.database.session import get_db

# Optional API key authentication 
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)):
    """
    Verify API key if provided
    """
    # If API key is not set in environment, skip verification
    required_api_key = os.getenv("API_KEY")
    if not required_api_key:
        return True
    
    # If environment has API key but request doesn't, raise error
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Verify API key
    if api_key != required_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    return True
