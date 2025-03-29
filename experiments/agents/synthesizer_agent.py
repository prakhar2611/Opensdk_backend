from agents import Agent
from src.utils.agent_hooks import CustomAgentHooks

def create_synthesizer_agent():
    """
    Creates and returns a synthesizer agent that combines results from other agents
    """
    synthesizer_agent = Agent(
        name="Synthesizer Agent",
        instructions="""
        You are a synthesizer agent that combines and interprets results from other agents.
        Your job is to:
        
        1. Review the information provided by other agents
        2. Correct any errors or inconsistencies
        3. Format the information in a clear, user-friendly way
        4. Provide a coherent final response
        
        Focus on making the data from different sources consistent and understandable.
        If there are missing pieces of information, note them clearly.
        If there are conflicting pieces of information, explain the conflicts.
        """,
        hooks=CustomAgentHooks(display_name="Synthesizer Agent"),
    )
    
    return synthesizer_agent 