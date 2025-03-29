from agents import Agent, function_tool
from utils.agent_hooks import CustomAgentHooks

@function_tool
def get_user_input(prompt: str) -> str:
    """
    Get input from the user with the provided prompt.
    """
    return input(prompt)

def create_user_input_agent():
    """
    Creates and returns the user input agent
    """
    user_input_agent = Agent(
        name="User Input Agent",
        instructions="""
        You are a helpful assistant that gets input from the user when needed.
        Use the get_user_input tool to prompt the user for information.
        Make your prompts clear and specific about what information you need.
        After getting the information, you can present it back to other agents.
        """,
        tools=[get_user_input],
        hooks=CustomAgentHooks(display_name="User Input Agent"),
    )
    
    return user_input_agent 