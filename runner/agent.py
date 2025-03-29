import os
from typing import Dict, List, Any, Union

from agents import Agent, function_tool
import logger
from tools.tools import get_tool_by_name
from utils import load_agents
from utils.agent_hooks import CustomAgentHooks
from models import Orchestrator, Agent as AgentModel, PromptField
from utils.ssl_utils import setup_ssl_bypass


class AgentModelExecutor:
    """Executes agents with agents SDK"""

    def __init__(self):
        """Initialize the agent executor"""
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Setup SSL bypass
        self.http_client = setup_ssl_bypass()
        logger.info("SSL bypass setup completed for agent executor")

    def initialize_agent_model(self, agentId: str) -> Agent:
        """Initialize the agent
        
        Args:
            agentId: The ID of the agent to initialize
            
        Returns:
            The initialized agent
            
        Raises:
            KeyError: If the agent ID is not found
        """
        try:
            # Getting the agent by id 
            agents_data = load_agents()
            agent_data = agents_data[agentId]

            # Converting the agent data to agent model
            agent_model = AgentModel.from_dict(agent_data)

            # Creating the agent from the model
            return self.create_agent_from_data(agent_model)
        except KeyError:
            logger.error(f"Agent with ID {agentId} not found")
            raise KeyError(f"Agent with ID {agentId} not found")
    
    def create_agent_from_data(self, agent_model: Union[AgentModel, str]) -> tuple:
        """Create an agent from model class or agent ID
        
        Args:
            agent_model: Either an AgentModel instance or a string agent ID
            
        Returns:
            A tuple containing (agent, description)
            
        Raises:
            TypeError: If the agent_model type is not supported
        """
        # If agent_model is a string (agent ID), load the agent model
        if isinstance(agent_model, str):
            agents_data = load_agents()
            agent_data = agents_data[agent_model]
            agent_model = AgentModel.from_dict(agent_data)
        elif not isinstance(agent_model, AgentModel):
            raise TypeError("agent_model must be either an AgentModel instance or a string agent ID")

        # Get tools based on selected_tools names
        tools = []
        for tool_name in agent_model.selected_tools:
            tool_def = get_tool_by_name(tool_name)
            if tool_def and 'function' in tool_def:
                tools.append(tool_def['function'])

        # Create the agent (without description parameter)
        agent = Agent(
            name=agent_model.name,
            instructions=agent_model.system_prompt,
            tools=tools,
            hooks=CustomAgentHooks(display_name=agent_model.name),
        )
        
        # Return both the agent and its description separately
        return agent, agent_model.description
    
    
    
