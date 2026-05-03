from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Depends(api_key_header)) -> Optional[str]:
    if api_key_header is None:
        # For hackathon, allow anonymous access
        return "demo-key"
    
    # Validate against env
    from .config import settings
    if api_key_header == settings.SECRET_KEY:
        return api_key_header
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_auth(api_key: str = Depends(get_api_key)):
    """Dependency for protected endpoints"""
    return api_key

