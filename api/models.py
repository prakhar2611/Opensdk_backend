from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# Agent models
class PromptFieldCreate(BaseModel):
    name: str
    description: str
    default_value: str
    required: bool = True

class AgentCreate(BaseModel):
    name: str
    system_prompt: str
    additional_prompt: Optional[str] = ""
    selected_tools: List[str]
    handoff: bool = False
    prompt_fields: List[PromptFieldCreate] = []

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    additional_prompt: Optional[str] = None
    selected_tools: Optional[List[str]] = None
    handoff: Optional[bool] = None
    prompt_fields: Optional[List[PromptFieldCreate]] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    system_prompt: str
    additional_prompt: Optional[str] = ""
    selected_tools: List[str]
    handoff: bool = False
    prompt_fields: List[Dict[str, Any]] = []

# Orchestrator models
class OrchestratorCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    agents: List[str]  # List of agent IDs
    tools: List[str]   # List of function tool names
    system_prompt: str

class OrchestratorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agents: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    system_prompt: Optional[str] = None

class OrchestratorResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    agents: List[str]
    tools: List[str]
    system_prompt: str

# Runner models
class AgentRunRequest(BaseModel):
    user_input: str
    prompt_field_values: Optional[Dict[str, str]] = {}

class OrchestratorRunRequest(BaseModel):
    user_input: str
    prompt_field_values: Optional[Dict[str, Any]] = {}
    save_history: bool = True

class RunResponse(BaseModel):
    response: str
    execution_details: Optional[Dict[str, Any]] = None
    token_usage: Optional[Dict[str, int]] = None
    cost: Optional[Dict[str, float]] = None 