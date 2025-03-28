# Utils module for the project 

import json
import os
import uuid
from typing import Dict, Any, List

def save_agents(agents: Dict[str, Any]) -> None:
    """
    Save agents to a JSON file.
    
    Args:
        agents (Dict[str, Any]): Dictionary of agents
    """
    with open("data/agents.json", "w") as f:
        json.dump(agents, f, indent=2)

def save_orchestrators(orchestrators: Dict[str, Any]) -> None:
    """
    Save orchestrators to a JSON file.
    
    Args:
        orchestrators (Dict[str, Any]): Dictionary of orchestrators
    """
    with open("data/orchestrators.json", "w") as f:
        json.dump(orchestrators, f, indent=2)

def load_agents() -> Dict[str, Any]:
    """
    Load agents from a JSON file.
    
    Returns:
        Dict[str, Any]: Dictionary of agents
    """
    if os.path.exists("data/agents.json"):
        with open("data/agents.json", "r") as f:
            return json.load(f)
    return {}

def load_orchestrators() -> Dict[str, Any]:
    """
    Load orchestrators from a JSON file.
    
    Returns:
        Dict[str, Any]: Dictionary of orchestrators
    """
    if os.path.exists("data/orchestrators.json"):
        with open("data/orchestrators.json", "r") as f:
            return json.load(f)
    return {}

def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        str: Unique ID
    """
    return str(uuid.uuid4())

def delete_agent(agent_id: str) -> bool:
    """
    Delete an agent by ID.
    
    Args:
        agent_id (str): ID of the agent to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    agents = load_agents()
    if agent_id in agents:
        # Check if agent is used in any orchestrator
        orchestrators = load_orchestrators()
        used_in_orchestrators = []
        
        for orch_id, orch_data in orchestrators.items():
            if agent_id in orch_data.get('agents', []):
                used_in_orchestrators.append(orch_data.get('name', f"Orchestrator {orch_id}"))
        
        if used_in_orchestrators:
            # Return False and the list of orchestrators using this agent
            return False, used_in_orchestrators
        
        # Remove the agent
        del agents[agent_id]
        save_agents(agents)
        return True, []
    
    return False, []

def delete_orchestrator(orchestrator_id: str) -> bool:
    """
    Delete an orchestrator by ID.
    
    Args:
        orchestrator_id (str): ID of the orchestrator to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    orchestrators = load_orchestrators()
    if orchestrator_id in orchestrators:
        del orchestrators[orchestrator_id]
        save_orchestrators(orchestrators)
        return True
    
    return False 