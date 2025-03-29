import os
from typing import Dict, List, Any

from agents import Agent, RunConfig, Runner, function_tool

from runner.modelProvider import CustomModelProvider
from .agent import AgentModelExecutor
import logger
from utils import load_agents, load_orchestrators
from utils.agent_hooks import CustomAgentHooks
from models import Orchestrator, Agent as AgentModel, PromptField
from utils.ssl_utils import setup_ssl_bypass


class OrchestratorModelExecutor:
    """Executes orchestrators with agents SDK"""

    agent_executor = AgentModelExecutor()

    def __init__(self):
        """Initialize the agent executor"""
       
        # Setup SSL bypass
        self.http_client = setup_ssl_bypass()
        logger.info("SSL bypass setup completed for agent executor")
        self.isOpenAI = os.getenv("IS_OPENAI") == "true"

    def modelProvider(self):
        if self.isOpenAI is False:
            return CustomModelProvider()
        
        return None

    def initialize_orchestrator_model(self, orchestratorId: str) -> Orchestrator:
        """Initialize the orchestrator
        
        Args:
            orchestratorId: The ID of the orchestrator to initialize
            
        Returns:
            The initialized orchestrator model
            
        Raises:
            KeyError: If the orchestrator ID is not found
        """
        try:
            orchestrator_data = load_orchestrators()
            orchestrator_dict = orchestrator_data[orchestratorId]
            # Convert the dictionary to an Orchestrator object
            orchestrator = Orchestrator.from_dict(orchestrator_dict)
            return orchestrator
        except KeyError:
            logger.error(f"Orchestrator with ID {orchestratorId} not found")
            raise KeyError(f"Orchestrator with ID {orchestratorId} not found")
    
    def create_orchestrator_from_data(self, orchestrator: Orchestrator) -> Agent:
        """Create an orchestrator from model class
        
        Args:
            orchestrator: The orchestrator model to create from
            
        Returns:
            The created orchestrator agent
        """
        # Getting OpenSdk Agents from the agent Id 
        agents = []
        agent_descriptions = {}
        
        for agent_id in orchestrator.agents:
            agent, description = self.agent_executor.create_agent_from_data(agent_id)
            agents.append(agent)
            agent_descriptions[agent.name] = description

        # Creating Agent as tool to give to orchestrator
        agent_tools = []
        for agent in agents:
            # Use the agent description if it exists, otherwise use a default description
            tool_description = agent_descriptions.get(agent.name, f"Tool to use the {agent.name} agent")
            agent_tools.append(agent.as_tool(tool_name=agent.name, tool_description=tool_description))

        # Creating orchestrator from the data (basically another agent with agents as tools)
        # Not supporting the normal function tool for now
        orchestrator_agent = Agent(
            name=orchestrator.name,
            tools=agent_tools,
            instructions=orchestrator.system_prompt,
            hooks=CustomAgentHooks(display_name=orchestrator.name)
        )

        return orchestrator_agent

    async def run_orchestrator_Id(self, orchestratorId: str, user_input: str) -> Any:
        """Run the orchestrator
        
        Args:
            orchestratorId: The ID of the orchestrator to run
            user_input: The user input to process
            
        Returns:
            The result of running the orchestrator
        """
        logger.info(f"Running orchestrator {orchestratorId} with user input {user_input}")
        try:
            orchestrator_model = self.initialize_orchestrator_model(orchestratorId)
            orchestrator = self.create_orchestrator_from_data(orchestrator_model)

            runConfig = RunConfig(tracing_disabled=False)
            
            if self.modelProvider() is not None:
                runConfig = RunConfig(tracing_disabled=False,model_provider=self.modelProvider())

            logger.info(f"Running orchestrator {orchestratorId} with user input {user_input} and runConfig {runConfig}")

            orchestrator_result = await Runner.run(
                orchestrator,
                user_input,
                run_config=runConfig
            )

            return orchestrator_result.final_output
        except Exception as e:
            logger.error(f"Error running orchestrator {orchestratorId}: {str(e)}")
            raise
