import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import asyncio
import sys
import datetime

# Import agents SDK
from agents import Agent, Runner, RunConfig

# Import utilities and models
from models import Orchestrator, Agent as AgentModel, PromptField
from utils import load_agents, load_orchestrators
from tools.tools import get_tool_by_name
import logger as logger
from utils.ssl_utils import setup_ssl_bypass

# Import the CustomAgentHooks class
from utils.agent_hooks import CustomAgentHooks

# Load environment variables
load_dotenv()

# Create directory for conversation history if it doesn't exist
os.makedirs("data/conversations", exist_ok=True)

# Function to generate dynamic form fields for agent prompt placeholders
def generate_agent_prompt_fields(agent_id: str) -> Dict[str, Any]:
    """
    Generate Streamlit form fields for agent prompt placeholders.
    
    Args:
        agent_id (str): ID of the agent
        
    Returns:
        Dict[str, Any]: Dictionary of field values entered by the user
    """
    # Load agents
    agents_data = load_agents()
    
    if agent_id not in agents_data:
        st.error(f"Agent with ID {agent_id} not found")
        return {}
    
    # Get agent data
    agent_data = agents_data[agent_id]
    
    # Create Agent model instance
    agent_model = AgentModel.from_dict(agent_data)
    
    # If no prompt fields are defined, generate them from placeholders
    if not agent_model.prompt_fields:
        agent_model.prompt_fields = agent_model.generate_default_prompt_fields()
        
        # Save the updated agent with prompt fields
        agents_data[agent_id] = agent_model.to_dict()
        from src.utils import save_agents
        save_agents(agents_data)
    
    # Create form for prompt fields
    user_values = {}
    
    # Display field name as header
    st.subheader(f"Dynamic fields for {agent_model.name}")
    
    # Generate form fields for each prompt field
    for field in agent_model.prompt_fields:
        value = st.text_input(
            f"{field.description} ({field.name})",
            value=field.default_value,
            key=f"prompt_field_{agent_id}_{field.name}"
        )
        user_values[field.name] = value
    
    return user_values

class AgentExecutor:
    """Executes agents with OpenAI API using the agents SDK"""
    
    def __init__(self):
        """Initialize the agent executor"""
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Setup SSL bypass
        self.http_client = setup_ssl_bypass()
        logger.info("SSL bypass setup completed for agent executor")
    
    async def run_agent(self, agent: Agent, user_input: str) -> Dict[str, Any]:
        """
        Run an agent using the agents SDK Runner.
        
        Args:
            agent (Agent): The agent to run
            user_input (str): The user's input/question
            
        Returns:
            Dict[str, Any]: Dictionary containing the agent's response, token usage, and cost
        """
        logger.info(f"Running agent: {agent.name}")
        
        try:
            # Enable trace collection mode to access token usage
            run_config = RunConfig(
                tracing_disabled=False
                # The following parameters are not supported in your version of the Agents SDK
                # collect_tool_step_trace=True,
                # collect_message_trace=True
            )
            
            # Run the agent using the Runner from the SDK
            result = await Runner.run(
                agent,
                user_input,
                run_config=run_config
            )
            
            # Extract token usage and cost information
            token_usage = {}
            cost_info = {}
            
            # Debug the entire result structure to find token usage
            logger.debug(f"Result type: {type(result)}")
            logger.debug(f"Result attributes: {dir(result)}")
            
            # Check if trace is available (OpenAI Agents SDK specific)
            if hasattr(result, 'trace'):
                logger.debug("Found trace attribute in result")
                try:
                    if hasattr(result.trace, 'usage'):
                        logger.debug(f"Usage found in trace: {result.trace.usage}")
                        usage_data = result.trace.usage
                        # Extract token usage
                        if isinstance(usage_data, dict):
                            token_usage = {
                                'prompt_tokens': usage_data.get('prompt_tokens', 0),
                                'completion_tokens': usage_data.get('completion_tokens', 0),
                                'total_tokens': usage_data.get('total_tokens', 0)
                            }
                        else:
                            token_usage = {
                                'prompt_tokens': getattr(usage_data, 'prompt_tokens', 0),
                                'completion_tokens': getattr(usage_data, 'completion_tokens', 0),
                                'total_tokens': getattr(usage_data, 'total_tokens', 0)
                            }
                        
                        # Calculate cost
                        prompt_cost_per_1k = 0.01  # $0.01 per 1K tokens for GPT-4 input
                        completion_cost_per_1k = 0.03  # $0.03 per 1K tokens for GPT-4 output
                        
                        prompt_tokens = token_usage.get('prompt_tokens', 0)
                        completion_tokens = token_usage.get('completion_tokens', 0)
                        
                        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
                        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
                        total_cost = prompt_cost + completion_cost
                        
                        cost_info = {
                            'prompt_cost': round(prompt_cost, 6),
                            'completion_cost': round(completion_cost, 6),
                            'total_cost': round(total_cost, 6)
                        }
                    # If no usage directly in trace, try looking through trace items
                    elif hasattr(result.trace, 'trace_items'):
                        for item in result.trace.trace_items:
                            if hasattr(item, 'usage') and item.usage:
                                logger.debug(f"Found usage in trace item: {item.usage}")
                                usage_data = item.usage
                                token_usage = {
                                    'prompt_tokens': getattr(usage_data, 'prompt_tokens', 0) if hasattr(usage_data, 'prompt_tokens') else usage_data.get('prompt_tokens', 0),
                                    'completion_tokens': getattr(usage_data, 'completion_tokens', 0) if hasattr(usage_data, 'completion_tokens') else usage_data.get('completion_tokens', 0),
                                    'total_tokens': getattr(usage_data, 'total_tokens', 0) if hasattr(usage_data, 'total_tokens') else usage_data.get('total_tokens', 0)
                                }
                                
                                # Calculate cost
                                prompt_cost_per_1k = 0.01
                                completion_cost_per_1k = 0.03
                                
                                prompt_tokens = token_usage.get('prompt_tokens', 0)
                                completion_tokens = token_usage.get('completion_tokens', 0)
                                
                                prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
                                completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
                                total_cost = prompt_cost + completion_cost
                                
                                cost_info = {
                                    'prompt_cost': round(prompt_cost, 6),
                                    'completion_cost': round(completion_cost, 6),
                                    'total_cost': round(total_cost, 6)
                                }
                                break
                except Exception as e:
                    logger.debug(f"Error accessing usage from trace: {str(e)}")
            
            # Try other methods to access usage data if trace approach didn't work
            if not token_usage:
                # Try to access usage information directly from the result object
                try:
                    # In some versions of the OpenAI API, usage is available in the choices array
                    if hasattr(result, 'usage'):
                        logger.debug(f"Found usage directly in result: {result.usage}")
                        if isinstance(result.usage, dict):
                            token_usage = {
                                'prompt_tokens': result.usage.get('prompt_tokens', 0),
                                'completion_tokens': result.usage.get('completion_tokens', 0),
                                'total_tokens': result.usage.get('total_tokens', 0)
                            }
                        else:
                            token_usage = {
                                'prompt_tokens': getattr(result.usage, 'prompt_tokens', 0),
                                'completion_tokens': getattr(result.usage, 'completion_tokens', 0),
                                'total_tokens': getattr(result.usage, 'total_tokens', 0)
                            }
                        
                        # Calculate cost based on token usage
                        prompt_cost_per_1k = 0.01  # $0.01 per 1K tokens for GPT-4 input
                        completion_cost_per_1k = 0.03  # $0.03 per 1K tokens for GPT-4 output
                        
                        prompt_tokens = token_usage.get('prompt_tokens', 0)
                        completion_tokens = token_usage.get('completion_tokens', 0)
                        
                        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
                        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
                        total_cost = prompt_cost + completion_cost
                        
                        cost_info = {
                            'prompt_cost': round(prompt_cost, 6),
                            'completion_cost': round(completion_cost, 6),
                            'total_cost': round(total_cost, 6)
                        }
                except Exception as e:
                    logger.debug(f"Error accessing usage from result: {str(e)}")
            
            # Try to access OpenAI specific data from the run property if previous approaches didn't work
            if not token_usage and hasattr(result, 'run'):
                try:
                    # In OpenAI Agents SDK, token usage might be in the run.usage property
                    if hasattr(result.run, 'usage') and result.run.usage:
                        logger.debug(f"Usage found in run: {result.run.usage}")
                        # Check if it's a dictionary or an object
                        if isinstance(result.run.usage, dict):
                            token_usage = {
                                'prompt_tokens': result.run.usage.get('prompt_tokens', 0),
                                'completion_tokens': result.run.usage.get('completion_tokens', 0),
                                'total_tokens': result.run.usage.get('total_tokens', 0)
                            }
                        else:
                            # Assume it's an object with attributes
                            token_usage = {
                                'prompt_tokens': getattr(result.run.usage, 'prompt_tokens', 0),
                                'completion_tokens': getattr(result.run.usage, 'completion_tokens', 0),
                                'total_tokens': getattr(result.run.usage, 'total_tokens', 0)
                            }
                        
                        # Calculate cost
                        prompt_cost_per_1k = 0.01  # $0.01 per 1K tokens for GPT-4 input
                        completion_cost_per_1k = 0.03  # $0.03 per 1K tokens for GPT-4 output
                        
                        prompt_tokens = token_usage.get('prompt_tokens', 0)
                        completion_tokens = token_usage.get('completion_tokens', 0)
                        
                        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
                        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
                        total_cost = prompt_cost + completion_cost
                        
                        cost_info = {
                            'prompt_cost': round(prompt_cost, 6),
                            'completion_cost': round(completion_cost, 6),
                            'total_cost': round(total_cost, 6)
                        }
                except Exception as e:
                    logger.debug(f"Error accessing usage from run: {str(e)}")
            
            # If we still don't have token usage, check for a response object that might have it
            if not token_usage and hasattr(result, 'response'):
                try:
                    if hasattr(result.response, 'usage'):
                        logger.debug(f"Usage found in response: {result.response.usage}")
                        usage_data = result.response.usage
                        token_usage = {
                            'prompt_tokens': getattr(usage_data, 'prompt_tokens', 0) if hasattr(usage_data, 'prompt_tokens') else usage_data.get('prompt_tokens', 0),
                            'completion_tokens': getattr(usage_data, 'completion_tokens', 0) if hasattr(usage_data, 'completion_tokens') else usage_data.get('completion_tokens', 0),
                            'total_tokens': getattr(usage_data, 'total_tokens', 0) if hasattr(usage_data, 'total_tokens') else usage_data.get('total_tokens', 0)
                        }
                        
                        # Calculate cost
                        prompt_cost_per_1k = 0.01
                        completion_cost_per_1k = 0.03
                        
                        prompt_tokens = token_usage.get('prompt_tokens', 0)
                        completion_tokens = token_usage.get('completion_tokens', 0)
                        
                        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
                        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
                        total_cost = prompt_cost + completion_cost
                        
                        cost_info = {
                            'prompt_cost': round(prompt_cost, 6),
                            'completion_cost': round(completion_cost, 6),
                            'total_cost': round(total_cost, 6)
                        }
                except Exception as e:
                    logger.debug(f"Error accessing usage from response: {str(e)}")
            
            # If we still don't have token usage, attempt to estimate from input and output lengths
            if not token_usage:
                try:
                    input_length = len(user_input)
                    output_length = len(result.final_output) if hasattr(result, 'final_output') else 0
                    
                    # Very rough estimation: 1 token ≈ 4 characters
                    estimated_prompt_tokens = input_length // 4
                    estimated_completion_tokens = output_length // 4
                    estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens
                    
                    logger.warning(f"No token usage found, using rough estimation: {estimated_total_tokens} tokens")
                    
                    token_usage = {
                        'prompt_tokens': estimated_prompt_tokens,
                        'completion_tokens': estimated_completion_tokens,
                        'total_tokens': estimated_total_tokens,
                        'is_estimated': True  # Flag to indicate this is an estimation
                    }
                    
                    # Calculate estimated cost
                    prompt_cost_per_1k = 0.01
                    completion_cost_per_1k = 0.03
                    
                    prompt_cost = (estimated_prompt_tokens / 1000) * prompt_cost_per_1k
                    completion_cost = (estimated_completion_tokens / 1000) * completion_cost_per_1k
                    total_cost = prompt_cost + completion_cost
                    
                    cost_info = {
                        'prompt_cost': round(prompt_cost, 6),
                        'completion_cost': round(completion_cost, 6),
                        'total_cost': round(total_cost, 6),
                        'is_estimated': True  # Flag to indicate this is an estimation
                    }
                except Exception as e:
                    logger.debug(f"Error estimating token usage: {str(e)}")
                    logger.warning("Could not find or estimate token usage data")
            
            return {
                "response": result.final_output,
                "token_usage": token_usage,
                "cost": cost_info
            }
            
        except Exception as e:
            error_message = f"Error while running agent: {str(e)}"
            logger.error(error_message)
            return {
                "response": error_message,
                "token_usage": {},
                "cost": {}
            }
    
    async def cleanup(self):
        """Cleanup resources when done"""
        if hasattr(self, 'http_client') and self.http_client:
            await self.http_client.aclose()
            logger.info("HTTP client closed successfully")


class OrchestratorExecutor:
    """Executes orchestrators with agents SDK"""
    
    def __init__(self):
        """Initialize the orchestrator executor"""
        self.agent_executor = AgentExecutor()
        logger.info("Orchestrator executor initialized")
    
    def create_agent_from_data(self, agent_data: Dict[str, Any], user_values: Dict[str, Any] = None) -> Agent:
        """
        Create an Agent instance from data.
        
        Args:
            agent_data (Dict[str, Any]): Agent data from JSON
            user_values (Dict[str, Any], optional): User-provided values to format into prompts
            
        Returns:
            Agent: The created agent instance
        """
        # Get tools based on selected_tools names
        tools = []
        for tool_name in agent_data.get('selected_tools', []):
            tool_def = get_tool_by_name(tool_name)
            if tool_def and 'function' in tool_def:
                tools.append(tool_def['function'])
        
        # Get agent name for display in hooks
        agent_name = agent_data.get('name', 'Unnamed Agent')
        
        # Log info about user values for debugging
        if user_values:
            logger.info(f"User values for agent {agent_name}: {user_values}")
            
            # Special handling for ClickHouse agents
            if any(tool in ['describe_table', 'run_query', 'show_tables'] for tool in agent_data.get('selected_tools', [])):
                logger.info(f"Agent {agent_name} is a ClickHouse agent")
                
                # Log key database values
                if 'database' in user_values:
                    logger.info(f"Database value: {user_values['database']}")
                else:
                    logger.warning(f"No database value provided for ClickHouse agent {agent_name}")
                
                # Process tables value if present
                if 'tables' in user_values:
                    tables_value = user_values['tables']
                    # If it's a comma-separated string, make sure it's properly formatted
                    if isinstance(tables_value, str) and ',' in tables_value:
                        tables_list = [t.strip() for t in tables_value.split(',')]
                        user_values['tables'] = tables_list
                        logger.info(f"Formatted tables string to list: {tables_list}")
                    logger.info(f"Tables value: {user_values['tables']}")
                else:
                    logger.warning(f"No tables value provided for ClickHouse agent {agent_name}")
        else:
            logger.warning(f"No user values provided for agent {agent_name} prompts")
        
        # Format system prompt with user values if provided
        system_prompt = agent_data.get('system_prompt', '')
        if user_values:
            try:
                system_prompt = system_prompt.format(**user_values)
                logger.info(f"Formatted system prompt for {agent_name}")
            except KeyError as e:
                logger.warning(f"Missing key in user_values for formatting prompt: {str(e)}")
                logger.warning(f"Available keys: {list(user_values.keys())}")
                logger.warning(f"Required keys: {self.extract_placeholders(system_prompt)}")
        
        # Create the agent with custom hooks
        agent = Agent(
            name=agent_name,
            instructions=system_prompt,
            tools=tools,
            hooks=CustomAgentHooks(display_name=agent_name)
        )
        
        # Format and add additional prompt if it exists
        if 'additional_prompt' in agent_data and agent_data['additional_prompt']:
            additional_prompt = agent_data['additional_prompt']
            if user_values:
                try:
                    additional_prompt = additional_prompt.format(**user_values)
                    logger.info(f"Formatted additional prompt for {agent_name}")
                except KeyError as e:
                    logger.warning(f"Missing key in user_values for formatting additional prompt: {str(e)}")
                    logger.warning(f"Available keys: {list(user_values.keys())}")
                    logger.warning(f"Required keys: {self.extract_placeholders(additional_prompt)}")
            agent.additional_prompt = additional_prompt
        
        return agent
    
    def extract_placeholders(self, text: str) -> List[str]:
        """Extract placeholder variables from text in {name} format"""
        import re
        if not text:
            return []
        
        # Find all {placeholder} patterns
        matches = re.findall(r'\{([a-zA-Z0-9_]+)\}', text)
        return list(set(matches))
    
    async def run_orchestrator(self, orchestrator: Orchestrator, user_input: str, user_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run an orchestrator by initializing agents and coordinating their execution.
        
        Args:
            orchestrator (Orchestrator): The orchestrator to run
            user_input (str): The user's input/question
            user_values (Dict[str, Any], optional): User-provided values to format into agent prompts
            
        Returns:
            Dict[str, Any]: Result containing orchestrator response, execution details, and token usage/cost
        """
        logger.info(f"Running orchestrator: {orchestrator.name}")
        
        result = {
            "response": "",
            "agent_calls": [],
            "execution_log": [],
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "cost": {
                "prompt_cost": 0,
                "completion_cost": 0,
                "total_cost": 0
            }
        }
        
        try:
            # Create all agent instances
            agents = []
            for agent_id in orchestrator.agents:
                # Load agent data
                agents_data = load_agents()
                if agent_id not in agents_data:
                    error_msg = f"Agent {agent_id} not found in agents data"
                    logger.error(error_msg)
                    result["execution_log"].append({"error": error_msg})
                    continue
                    
                agent_data = agents_data[agent_id]
                
                # Create agent instance
                agent = self.create_agent_from_data(agent_data, user_values)
                agents.append((agent_id, agent))
                
                # Log debug info
                if 'additional_prompt' in agent_data:
                    debug_msg = f"Agent {agent_id} loaded with additional prompt: {agent.additional_prompt}"
                    logger.debug(debug_msg)
                    
            # Run all agents in sequence
            for i, (agent_id, agent) in enumerate(agents):
                logger.info(f"Running agent {i+1}/{len(agents)}: {agent.name}")
                
                # Run the agent
                agent_result = await self.agent_executor.run_agent(agent, user_input)
                
                # Extract response and execution details
                agent_response = agent_result["response"]
                agent_token_usage = agent_result.get("token_usage", {})
                agent_cost = agent_result.get("cost", {})
                
                # Accumulate token usage and cost
                result["token_usage"]["prompt_tokens"] += agent_token_usage.get("prompt_tokens", 0)
                result["token_usage"]["completion_tokens"] += agent_token_usage.get("completion_tokens", 0)
                result["token_usage"]["total_tokens"] += agent_token_usage.get("total_tokens", 0)
                
                result["cost"]["prompt_cost"] += agent_cost.get("prompt_cost", 0)
                result["cost"]["completion_cost"] += agent_cost.get("completion_cost", 0)
                result["cost"]["total_cost"] += agent_cost.get("total_cost", 0)
                
                # Add to agent calls
                result["agent_calls"].append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "response": agent_response,
                    "token_usage": agent_token_usage,
                    "cost": agent_cost
                })
                
                # Set as final response
                result["response"] = agent_response
                
                # Log results
                logger.info(f"Agent {agent.name} responded: {agent_response[:100]}...")
                logger.info(f"Token usage: {agent_token_usage}")
                logger.info(f"Cost: {agent_cost}")
                
                # Stop if this is the last agent or if handoff is disabled
                if i == len(agents) - 1 or not agent_data.get('handoff', False):
                    break
                    
                # Otherwise, modify user input for next agent
                user_input = agent_response
                
            # Round cost values for display
            result["cost"]["prompt_cost"] = round(result["cost"]["prompt_cost"], 6)
            result["cost"]["completion_cost"] = round(result["cost"]["completion_cost"], 6) 
            result["cost"]["total_cost"] = round(result["cost"]["total_cost"], 6)
                
            logger.info(f"Orchestrator completed. Total tokens: {result['token_usage']['total_tokens']}, Total cost: ${result['cost']['total_cost']}")
            
        except Exception as e:
            error_message = f"Error while running orchestrator: {str(e)}"
            logger.error(error_message)
            result["execution_log"].append({"error": error_message})
            result["response"] = error_message
        
        return result


# Helper function to run an orchestrator by ID
async def run_orchestrator_by_id(orchestrator_id: str, user_input: str, user_values: Dict[str, Any] = None, save_history: bool = True) -> Dict[str, Any]:
    """
    Run an orchestrator by its ID.
    
    Args:
        orchestrator_id (str): ID of the orchestrator to run
        user_input (str): The user's input/question
        user_values (Dict[str, Any], optional): User-provided values to format into agent prompts
        save_history (bool): Whether to save the exchange to conversation history
        
    Returns:
        Dict[str, Any]: Result containing orchestrator response, execution details, and token usage/cost
    """
    logger.info(f"Running orchestrator by ID: {orchestrator_id}")
    
    # Load orchestrators
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        error_message = f"Orchestrator with ID {orchestrator_id} not found"
        logger.error(error_message)
        return {
            "response": error_message,
            "execution_details": {"error": error_message},
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "cost": {"prompt_cost": 0, "completion_cost": 0, "total_cost": 0}
        }
    
    # Create orchestrator
    orchestrator_data = orchestrators_data[orchestrator_id]
    orchestrator = Orchestrator.from_dict(orchestrator_data)
    
    # Create executor
    executor = OrchestratorExecutor()
    
    # Run orchestrator
    try:
        result = await executor.run_orchestrator(orchestrator, user_input, user_values)
        
        # Save to conversation history if required
        if save_history:
            save_to_conversation_history(orchestrator_id, user_input, result["response"], user_values)
            
        return result
    finally:
        # Cleanup executor resources
        await executor.agent_executor.cleanup()
        logger.info("Executor resources cleaned up")

def load_conversation_history(orchestrator_id: str) -> List[Dict[str, Any]]:
    """
    Load conversation history for a specific orchestrator.
    
    Args:
        orchestrator_id (str): ID of the orchestrator
        
    Returns:
        List[Dict[str, Any]]: Conversation history
    """
    history_file = f"data/conversations/{orchestrator_id}.json"
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding conversation history file for orchestrator {orchestrator_id}")
            return []
    
    return []

def save_conversation_history(orchestrator_id: str, history: List[Dict[str, Any]]) -> None:
    """
    Save conversation history for a specific orchestrator.
    
    Args:
        orchestrator_id (str): ID of the orchestrator
        history (List[Dict[str, Any]]): Conversation history
    """
    history_file = f"data/conversations/{orchestrator_id}.json"
    
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def save_to_conversation_history(orchestrator_id: str, user_input: str, response: str, user_values: Optional[Dict[str, Any]] = None) -> None:
    """
    Add a new exchange to the conversation history.
    
    Args:
        orchestrator_id (str): ID of the orchestrator
        user_input (str): User input/question
        response (str): Response from the orchestrator
        user_values (Dict[str, Any], optional): User-provided values used in the query
    """
    # Load existing history
    history = load_conversation_history(orchestrator_id)
    
    # Prepare the new entry
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user": user_input,
        "response": response
    }
    
    # Add user values if provided
    if user_values:
        entry["user_values"] = user_values
    
    # Add to history
    history.append(entry)
    
    # Save updated history
    save_conversation_history(orchestrator_id, history)
    logger.info(f"Added new exchange to conversation history for orchestrator {orchestrator_id}")

def get_conversation_history(orchestrator_id: str) -> List[Dict[str, Any]]:
    """
    Get the conversation history for a specific orchestrator.
    
    Args:
        orchestrator_id (str): ID of the orchestrator
        
    Returns:
        List[Dict[str, Any]]: Conversation history
    """
    return load_conversation_history(orchestrator_id)
