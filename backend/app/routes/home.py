from fastapi import APIRouter, HTTPException
from typing import Dict

home_route = APIRouter()


@home_route.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {"status": "healthy"}

@home_route.get("/",
                response_model=Dict[str, str],
                summary="Root endpoint",
                description="Returns a welcome message")
async def index() -> str:
    try:
        return {"message": "Welcome to Event planner API!"}
    except:
        raise HTTPException(status_code=500, detail="Internal server error")