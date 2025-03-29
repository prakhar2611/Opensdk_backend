from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class FunctionTool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class PromptField(BaseModel):
    """Defines a dynamic field that can be replaced in the prompt."""
    name: str
    description: str
    default_value: str
    required: bool = True

class Agent(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    system_prompt: str
    additional_prompt: Optional[str] = ""
    selected_tools: List[str]
    handoff: bool = False
    prompt_fields: List[PromptField] = []
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "additional_prompt": self.additional_prompt,
            "selected_tools": self.selected_tools,
            "handoff": self.handoff,
            "prompt_fields": [field.dict() for field in self.prompt_fields] if self.prompt_fields else []
        }
    
    @classmethod
    def from_dict(cls, data):
        prompt_fields = []
        if "prompt_fields" in data and data["prompt_fields"]:
            prompt_fields = [PromptField(**field) for field in data["prompt_fields"]]
            
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            system_prompt=data["system_prompt"],
            additional_prompt=data.get("additional_prompt", ""),
            selected_tools=data["selected_tools"],
            handoff=data.get("handoff", False),
            prompt_fields=prompt_fields
        )
        
    def extract_prompt_placeholders(self) -> List[str]:
        """Extract all placeholder variables from the system prompt and additional prompt."""
        import re
        
        placeholders = set()
        for text in [self.system_prompt, self.additional_prompt]:
            if not text:
                continue
                
            # Find all {placeholder} patterns in the text
            matches = re.findall(r'\{([a-zA-Z0-9_]+)\}', text)
            placeholders.update(matches)
        
        return list(placeholders)
    
    def generate_default_prompt_fields(self) -> List[PromptField]:
        """Generate default prompt fields based on placeholders in the prompt."""
        placeholders = self.extract_prompt_placeholders()
        
        return [
            PromptField(
                name=placeholder,
                description=f"Value for {placeholder}",
                default_value="",
                required=True
            )
            for placeholder in placeholders
        ]

class Orchestrator(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    agents: List[str]  # List of agent IDs
    tools: List[str]   # List of function tool names
    system_prompt: str
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agents": self.agents,
            "tools": self.tools,
            "system_prompt": self.system_prompt
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            agents=data["agents"],
            tools=data["tools"],
            system_prompt=data["system_prompt"]
        ) 