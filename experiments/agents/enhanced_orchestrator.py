from agents import Agent
from agents.enhanced_tools import enhanced_clickhouse_query
from utils.agent_hooks import CustomAgentHooks
from agents.clickhouse_agent import create_clickhouse_agent
from agents.user_input_agent import create_user_input_agent

def create_enhanced_orchestrator_agent():
    """
    Creates and returns an enhanced orchestrator agent that modifies user input
    when delegating to other agents
    """
    # Create the agents that will be used as tools
    clickhouse_agent = create_clickhouse_agent(database="user_cohort_v2", tables=["monthly_seller_atg_brand"])
    user_input_agent = create_user_input_agent()
    
    # Create the orchestrator agent
    orchestrator_agent = Agent(
        name="Enhanced Orchestrator Agent",
        instructions="""
        You are an intelligent orchestrator that helps users interact with ClickHouse databases.
        Your job is to coordinate between different specialized agents and enhance the user input
        with additional context when needed.
        
        When delegating to the ClickHouse agent, you can append or modify the user's input to include:
        - Table names when mentioned by the user
        - Database context information
        - Derived SQL queries based on natural language requests
        - Additional metadata that helps the ClickHouse agent understand the request better
        
        For example:
        - If user asks about "data in the users table", append the actual table name as context
        - If user asks to "show me recent orders", transform this into a more specific query for the ClickHouse agent
        
        When using the User Input agent, you can:
        - Ask for specific table names, query parameters, or database details
        - Then use that information to enhance the context when delegating to the ClickHouse agent
        
        Example workflow:
        1. User asks: "Show me data from the users table"
        2. You enhance this to: "Show me data from the users table (table_name: users, action: select)"
        3. Then delegate to the ClickHouse agent with this enhanced context
        
        Never try to perform the tasks yourself - always delegate to the appropriate specialized agent
        after enhancing the context as needed.
        """,
        tools=[
            clickhouse_agent.as_tool(
                tool_name="use_clickhouse_agent",
                tool_description="Use the ClickHouse database agent to perform database operations. You can enhance the user's query with additional context when calling this tool."
            ),
            user_input_agent.as_tool(
                tool_name="get_user_input",
                tool_description="Use the User Input agent to get additional information from the user"
            ),
            enhanced_clickhouse_query
        ],
        hooks=CustomAgentHooks(display_name="Enhanced Orchestrator Agent"),
    )
    
    return orchestrator_agent

# Example usage in main.py:
"""
# Instead of creating the standard orchestrator:
# orchestrator_agent = create_orchestrator_agent()

# Create the enhanced orchestrator that modifies user input:
orchestrator_agent = create_enhanced_orchestrator_agent()

# When the orchestrator calls the ClickHouse agent, it can now enhance the user input
# For example, if user asks: "Show data from users"
# The orchestrator might call the ClickHouse agent with: 
# "Show data from users table. Context: {table: 'users', action: 'select', limit: 10}"
""" 