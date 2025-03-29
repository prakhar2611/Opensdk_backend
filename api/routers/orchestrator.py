from fastapi import APIRouter, HTTPException, Body, Path, Query, Depends
from typing import List, Dict, Any, Optional
import os
import sys
import asyncio
from runner.orchestrator import OrchestratorModelExecutor

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import existing functionality
from models import Orchestrator
from utils import (
    load_orchestrators, save_orchestrators,
    generate_id, delete_orchestrator, load_agents
)
from tools.tools import get_available_tools
from executor import (
    run_orchestrator_by_id, get_conversation_history,
    save_to_conversation_history
)

# Import API models
from api.models import (
    OrchestratorCreate, OrchestratorUpdate, OrchestratorResponse,
    OrchestratorRunRequest, RunResponse
)

router = APIRouter(
    prefix="/orchestrators",
    tags=["Orchestrators"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
def orchestrator_to_response(orch_id: str, orch_data: Dict[str, Any]) -> OrchestratorResponse:
    """Convert orchestrator data to response model"""
    return OrchestratorResponse(
        id=orch_id,
        name=orch_data["name"],
        description=orch_data.get("description", ""),
        agents=orch_data["agents"],
        tools=orch_data["tools"],
        system_prompt=orch_data["system_prompt"]
    )

# GET all orchestrators
@router.get("/", response_model=List[OrchestratorResponse])
async def get_all_orchestrators():
    """Get all orchestrators"""
    orchestrators_data = load_orchestrators()
    return [
        orchestrator_to_response(orch_id, orch_data)
        for orch_id, orch_data in orchestrators_data.items()
    ]

# GET orchestrator by ID
@router.get("/{orchestrator_id}", response_model=OrchestratorResponse)
async def get_orchestrator(orchestrator_id: str = Path(..., description="The ID of the orchestrator to get")):
    """Get a specific orchestrator by ID"""
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    return orchestrator_to_response(orchestrator_id, orchestrators_data[orchestrator_id])

# POST new orchestrator
@router.post("/", response_model=OrchestratorResponse, status_code=201)
async def create_orchestrator(orchestrator: OrchestratorCreate):
    """Create a new orchestrator"""
    orchestrators_data = load_orchestrators()
    agents_data = load_agents()
    
    # Validate that all agent IDs exist
    for agent_id in orchestrator.agents:
        if agent_id not in agents_data:
            raise HTTPException(status_code=400, detail=f"Agent with ID {agent_id} not found")
    
    # Generate ID for new orchestrator
    orchestrator_id = generate_id()
    
    # Create new orchestrator data
    new_orchestrator = Orchestrator(
        id=orchestrator_id,
        name=orchestrator.name,
        description=orchestrator.description,
        agents=orchestrator.agents,
        tools=orchestrator.tools,
        system_prompt=orchestrator.system_prompt
    )
    
    # Add to orchestrators data
    orchestrators_data[orchestrator_id] = new_orchestrator.to_dict()
    
    # Save orchestrators data
    save_orchestrators(orchestrators_data)
    
    return orchestrator_to_response(orchestrator_id, orchestrators_data[orchestrator_id])

# PUT update orchestrator
@router.put("/{orchestrator_id}", response_model=OrchestratorResponse)
async def update_orchestrator(
    orchestrator: OrchestratorUpdate,
    orchestrator_id: str = Path(..., description="The ID of the orchestrator to update")
):
    """Update an existing orchestrator"""
    orchestrators_data = load_orchestrators()
    agents_data = load_agents()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    # Get existing orchestrator data
    orch_data = orchestrators_data[orchestrator_id]
    
    # Update fields if provided
    if orchestrator.name is not None:
        orch_data["name"] = orchestrator.name
    if orchestrator.description is not None:
        orch_data["description"] = orchestrator.description
    if orchestrator.system_prompt is not None:
        orch_data["system_prompt"] = orchestrator.system_prompt
    
    # Validate and update agent IDs if provided
    if orchestrator.agents is not None:
        for agent_id in orchestrator.agents:
            if agent_id not in agents_data:
                raise HTTPException(status_code=400, detail=f"Agent with ID {agent_id} not found")
        orch_data["agents"] = orchestrator.agents
    
    # Update tools if provided
    if orchestrator.tools is not None:
        orch_data["tools"] = orchestrator.tools
    
    # Save updated orchestrators data
    save_orchestrators(orchestrators_data)
    
    return orchestrator_to_response(orchestrator_id, orch_data)

# DELETE orchestrator
@router.delete("/{orchestrator_id}", status_code=204)
async def remove_orchestrator(orchestrator_id: str = Path(..., description="The ID of the orchestrator to delete")):
    """Delete an orchestrator"""
    if not delete_orchestrator(orchestrator_id):
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    return None

# POST run orchestrator
@router.post("/{orchestrator_id}/run", response_model=RunResponse)
async def run_orchestrator(
    run_request: OrchestratorRunRequest,
    orchestrator_id: str = Path(..., description="The ID of the orchestrator to run")
):
    """Run an orchestrator with user input"""
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    try:
        orchestrator_executor = OrchestratorModelExecutor()
        # Run orchestrator
        result = await orchestrator_executor.run_orchestrator_Id(
            orchestratorId=orchestrator_id,
            user_input=run_request.user_input
        )
        
        return RunResponse(
            response=result,
            execution_details={
                "orchestrator_id": orchestrator_id,
                "orchestrator_name": orchestrators_data[orchestrator_id]["name"],
                # "agent_calls": result.get("agent_calls", []),
                # "execution_log": result.get("execution_log", [])
            }
        )
        
    except Exception as e:
        # Re-raise as HTTP exception
        raise HTTPException(status_code=500, detail=f"Error running orchestrator: {str(e)}")

# GET conversation history for orchestrator
@router.get("/{orchestrator_id}/history", response_model=List[Dict[str, Any]])
async def get_history(orchestrator_id: str = Path(..., description="The ID of the orchestrator")):
    """Get conversation history for an orchestrator"""
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    return get_conversation_history(orchestrator_id) 