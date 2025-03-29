from agents import Agent
from src.utils.agent_hooks import CustomAgentHooks
from experiments.agents.clickhouse_agent import create_clickhouse_agent
from experiments.agents.user_input_agent import create_user_input_agent
from experiments.agents.analyst_agent import create_analyst_agent
from experiments.agents.visualization_agent import create_visualization_agent

def create_orchestrator_agent():
    """
    Creates and returns the orchestrator agent that coordinates between the ClickHouse and User Input agents
    """
    # Create the agents that will be used as tools
    clickhouse_agent = create_clickhouse_agent(database="user_cohort_v2", tables=["monthly_seller_atg_brand"])
    # analyst_agent = create_analyst_agent()
    visualization_agent = create_visualization_agent()
    
    # Create the orchestrator agent
    orchestrator_agent = Agent(
        name="Orchestrator Agent",
        instructions="""
        You are an intelligent orchestrator that helps users interact with ClickHouse databases and analyze data.
        Your job is to coordinate between different specialized agents:
        
        1. The ClickHouse Agent: For database operations and queries
        2. The Analyst Agent: For analyzing data with advanced methods like finding outliers and correlations
        3. The Visualization Agent: For generating visual representations of data

        Based on the user's request, determine which agent is best suited to handle it:
        - For database queries, exploring schema, or running SQL, use the ClickHouse agent
        - For data analysis like finding outliers or correlations, use the Analyst agent
        - For data visualization, use the Visualization agent
        
        Typical workflow:
        1. Use the ClickHouse agent to retrieve the data
        2. Depending on the user's goal:
           - Pass the data to the Analyst agent for analysis
           - Pass the data to the Visualization agent for visualization
           - Or do both if appropriate

        For data visualization:
        - First retrieve data using the ClickHouse agent
        - Then pass that data to the Visualization agent
        - For time series data, ensure the date/time column is properly formatted
        
        IMPORTANT: When using the Visualization agent's function tools, always pass the parameters in JSON format:
        - For analyze_data_for_visualization: Format as {"data": [your_data_array]}
        - For visualize_data: Format as {"data": [your_data_array], "title": "Your Title"}
        - For save_visualization: Format as {"data": [your_data_array], "filename": "your_filename", "title": "Your Title"}

        When using the Analyst agent's function tools:
        - For find_outliers: Pass the data from ClickHouse query as the 'data' parameter
        - For find_correlation: Pass the data from ClickHouse query as the 'data' parameter

        Never try to perform the tasks yourself - always delegate to the appropriate specialized agent.
        Coordinate the flow between agents to provide a seamless experience to the user.
        """,
        tools=[
            clickhouse_agent.as_tool(
                tool_name="use_clickhouse_agent",
                tool_description="Use the ClickHouse database agent to perform database operations. You can enhance the user's query with additional context when calling this tool."
            ),
            
            # analyst_agent.as_tool(
            #     tool_name="use_analyst_agent",
            #     tool_description="Use this agent to analyze data with methods like finding outliers and correlations. When using function tools like find_outliers or find_correlation, pass the data from ClickHouse query results as the 'data' parameter."
            # ),
            
            visualization_agent.as_tool(
                tool_name="use_visualization_agent",
                tool_description="Use this agent to visualize data from ClickHouse queries. It can analyze data for visualization possibilities, generate HTML visualizations, and save them to files. IMPORTANT: When calling function tools, pass the parameters in JSON format."
            )
        ],
        hooks=CustomAgentHooks(display_name="Orchestrator Agent"),
    )
    
    return orchestrator_agent 