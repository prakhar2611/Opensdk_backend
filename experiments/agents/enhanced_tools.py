from agents import function_tool
from typing import Dict, Any, Optional

@function_tool
def enhanced_clickhouse_query(
    user_query: str, 
    table_name: Optional[str] = None, 
    database: Optional[str] = None, 
    limit: Optional[int] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enhanced tool to query ClickHouse with additional context.
    This function demonstrates how to enhance a user query with additional context
    before passing it to the ClickHouse agent.
    
    Args:
        user_query: The original user query
        table_name: Optional table name to include in context
        database: Optional database name to include in context
        limit: Optional row limit to apply
        additional_context: Optional dictionary with any additional context
        
    Returns:
        Enhanced query string with context metadata that can be passed to ClickHouse agent
    """
    # Start with the original query
    enhanced_query = user_query
    
    # Construct a metadata section with structured information
    metadata = {}
    
    if table_name:
        metadata["table"] = table_name
    
    if database:
        metadata["database"] = database
    
    if limit:
        metadata["limit"] = limit
    
    if additional_context:
        metadata.update(additional_context)
    
    # Only add metadata section if we have metadata
    if metadata:
        # Format the metadata as a string
        metadata_str = ", ".join([f"{k}: '{v}'" for k, v in metadata.items()])
        enhanced_query = f"{enhanced_query}\n\nContext: {{{metadata_str}}}"
    
    return enhanced_query


# Example usage in the orchestrator agent
"""
How to use in orchestrator_agent.py:

from src.agents.enhanced_tools import enhanced_clickhouse_query

def create_orchestrator_agent():
    # Create agents
    clickhouse_agent = create_clickhouse_agent()
    user_input_agent = create_user_input_agent()
    
    # Create the orchestrator agent
    orchestrator_agent = Agent(
        name="Orchestrator Agent",
        instructions="...",
        tools=[
            clickhouse_agent.as_tool(
                tool_name="use_clickhouse_agent",
                tool_description="Use the ClickHouse database agent to perform database operations"
            ),
            user_input_agent.as_tool(
                tool_name="get_user_input",
                tool_description="Use the User Input agent to get additional information from the user"
            ),
            enhanced_clickhouse_query,  # Add the enhanced query tool
        ],
        hooks=CustomAgentHooks(display_name="Orchestrator Agent"),
    )
    
    return orchestrator_agent
"""

# Example workflow:
"""
1. User asks: "Show me recent sales data"
2. Orchestrator recognizes this is about sales data and calls enhanced_clickhouse_query:
   
   enhanced_clickhouse_query(
       user_query="Show me recent sales data", 
       table_name="sales", 
       limit=10,
       additional_context={"sort_by": "timestamp", "order": "desc"}
   )
   
   This produces an enhanced query:
   "Show me recent sales data
   
   Context: {table: 'sales', limit: '10', sort_by: 'timestamp', order: 'desc'}"

3. This enhanced query is then passed to the ClickHouse agent, which has more context to work with
""" 