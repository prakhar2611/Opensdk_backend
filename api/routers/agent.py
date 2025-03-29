from fastapi import APIRouter, HTTPException, Body, Path, Query, Depends
from typing import List, Dict, Any, Optional
import os
import sys
import asyncio

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import existing functionality
from models import Agent, PromptField
from utils import (
    load_agents, save_agents, 
    generate_id, delete_agent
)
from tools.tools import get_available_tools
from executor import AgentExecutor

# Import API models
from api.models import (
    AgentCreate, AgentUpdate, AgentResponse,
    AgentRunRequest, RunResponse
)

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
def agent_to_response(agent_id: str, agent_data: Dict[str, Any]) -> AgentResponse:
    """Convert agent data to response model"""
    return AgentResponse(
        id=agent_id,
        name=agent_data["name"],
        description=agent_data.get("description", ""),
        system_prompt=agent_data["system_prompt"],
        additional_prompt=agent_data.get("additional_prompt", ""),
        selected_tools=agent_data["selected_tools"],
        handoff=agent_data.get("handoff", False),
        prompt_fields=agent_data.get("prompt_fields", [])
    )

# GET all agents
@router.get("/", response_model=List[AgentResponse])
async def get_all_agents():
    """Get all agents"""
    agents_data = load_agents()
    return [
        agent_to_response(agent_id, agent_data)
        for agent_id, agent_data in agents_data.items()
    ]

# GET agent by ID
@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str = Path(..., description="The ID of the agent to get")):
    """Get a specific agent by ID"""
    agents_data = load_agents()
    
    if agent_id not in agents_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent_to_response(agent_id, agents_data[agent_id])

# POST new agent
@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(agent: AgentCreate):
    """Create a new agent"""
    agents_data = load_agents()
    
    # Generate ID for new agent
    agent_id = generate_id()
    
    # Convert prompt fields to dict
    prompt_fields = [field.dict() for field in agent.prompt_fields] if agent.prompt_fields else []
    
    # Create new agent data
    new_agent = Agent(
        id=agent_id,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        additional_prompt=agent.additional_prompt,
        selected_tools=agent.selected_tools,
        handoff=agent.handoff,
        prompt_fields=[PromptField(**field) for field in prompt_fields]
    )
    
    # Add to agents data
    agents_data[agent_id] = new_agent.to_dict()
    
    # Save agents data
    save_agents(agents_data)
    
    return agent_to_response(agent_id, agents_data[agent_id])

# PUT update agent
@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent: AgentUpdate,
    agent_id: str = Path(..., description="The ID of the agent to update")
):
    """Update an existing agent"""
    agents_data = load_agents()
    
    if agent_id not in agents_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get existing agent data
    agent_data = agents_data[agent_id]
    
    # Update fields if provided
    if agent.name is not None:
        agent_data["name"] = agent.name
    if agent.description is not None:
        agent_data["description"] = agent.description
    if agent.system_prompt is not None:
        agent_data["system_prompt"] = agent.system_prompt
    if agent.additional_prompt is not None:
        agent_data["additional_prompt"] = agent.additional_prompt
    if agent.selected_tools is not None:
        agent_data["selected_tools"] = agent.selected_tools
    if agent.handoff is not None:
        agent_data["handoff"] = agent.handoff
    if agent.prompt_fields is not None:
        agent_data["prompt_fields"] = [field.dict() for field in agent.prompt_fields]
    
    # Save updated agents data
    save_agents(agents_data)
    
    return agent_to_response(agent_id, agent_data)

# DELETE agent
@router.delete("/{agent_id}", status_code=204)
async def remove_agent(agent_id: str = Path(..., description="The ID of the agent to delete")):
    """Delete an agent"""
    success, used_in = delete_agent(agent_id)
    
    if not success:
        if used_in:
            # Agent is used in orchestrators
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete agent because it is used in orchestrators: {', '.join(used_in)}"
            )
        else:
            # General error
            raise HTTPException(status_code=404, detail="Agent not found")
    
    return None

# GET available tools
@router.get("/tools/available", response_model=List[Dict[str, Any]])
async def get_tools():
    """Get all available function tools for agents"""
    return get_available_tools()

# POST run agent
@router.post("/{agent_id}/run", response_model=RunResponse)
async def run_agent(
    run_request: AgentRunRequest,
    agent_id: str = Path(..., description="The ID of the agent to run")
):
    """Run an agent with user input"""
    agents_data = load_agents()
    
    if agent_id not in agents_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_data = agents_data[agent_id]
    
    # Initialize agent executor
    agent_executor = AgentExecutor()
    
    try:
        # Create agent model
        agent_model = Agent.from_dict(agent_data)
        
        # Create agent using the executor's method that formats prompts with user values
        agent_instance = agent_executor.create_agent_from_data(agent_data, run_request.prompt_field_values)
        
        # Run the agent
        response = await agent_executor.run_agent(agent_instance, run_request.user_input)
        
        # Clean up
        await agent_executor.cleanup()
        
        return RunResponse(
            response=response,
            execution_details={"agent_id": agent_id, "agent_name": agent_data["name"]}
        )
    except Exception as e:
        # Clean up in case of error
        await agent_executor.cleanup()
        
        # Re-raise as HTTP exception
        raise HTTPException(status_code=500, detail=f"Error running agent: {str(e)}") 