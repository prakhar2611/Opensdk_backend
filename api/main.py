from fastapi import FastAPI, HTTPException, Body, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional
import os
import sys
import json
from dotenv import load_dotenv
import asyncio
import uuid

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing functionality
from models import Agent, Orchestrator, PromptField
from utils import (
    load_agents, load_orchestrators, save_agents, save_orchestrators,
    generate_id, delete_agent, delete_orchestrator
)
from executor import (
    run_orchestrator_by_id, get_conversation_history,
    save_to_conversation_history
)
from tools.tools import get_available_tools, get_tool_by_name

# Import routers
from api.routers.agent import router as agent_router
from api.routers.orchestrator import router as orchestrator_router
from api.routers.conversation import router as conversation_router

# Load environment variables
load_dotenv()

# Create app instance
app = FastAPI(
    title="Agent & Orchestrator API",
    description="API for managing and running AI agents and orchestrators",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Include routers
app.include_router(agent_router)
app.include_router(orchestrator_router)
app.include_router(conversation_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "ok", "message": "API is operational"}

# Root endpoint
@app.get("/")
async def root():
    """Get API information"""
    return {
        "name": "Agent & Orchestrator API",
        "version": "1.0.0",
        "description": "API for managing and running AI agents and orchestrators",
        "endpoints": {
            "agents": "/agents",
            "orchestrators": "/orchestrators",
            "conversations": "/conversations",
            "health": "/health",
            "docs": "/docs"
        }
    } 