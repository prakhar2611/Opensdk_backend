import asyncio
import os
from dotenv import load_dotenv

from agents import ItemHelpers, MessageOutputItem, Runner, trace, RunConfig
from utils.ssl_utils import setup_ssl_bypass
from utils.clickhouse_utils import check_db_connectivity
from experiments.agents import (
    create_clickhouse_agent,
    create_user_input_agent,
    create_synthesizer_agent
)
from experiments.agents.enhanced_orchestrator import create_enhanced_orchestrator_agent

# Load environment variables from .env file
load_dotenv()

async def main():
    """
    Main function to run the application with the enhanced orchestrator
    that demonstrates modifying user input when delegating to other agents
    """
    # Set up SSL bypass
    #http_client = setup_ssl_bypass()
    
    try:
        print("🔍 Enhanced ClickHouse Explorer 🔍")
        print("=" * 50)
        print("This version demonstrates how to modify/enhance user input when orchestrating between agents")
        print("=" * 50)
        
        # Check database connectivity before proceeding
        if not check_db_connectivity():
            print("❌ Cannot connect to ClickHouse database. Please check your connection settings.")
            return
        
        # Run the orchestration in a single trace
        with trace("Enhanced ClickHouse Explorer Session"):
            # Get initial user query
            user_query = input("\n🤔 What would you like to do with ClickHouse? ")
            
            # Create agents - using the enhanced orchestrator instead of the standard one
            orchestrator_agent = create_enhanced_orchestrator_agent()
            synthesizer_agent = create_synthesizer_agent()
            
            # Run the orchestrator with the enhanced capabilities
            print("\n🔄 Processing your request with enhanced context...\n")
            orchestrator_result = await Runner.run(
                orchestrator_agent, 
                user_query,
                run_config=RunConfig(
                    tracing_disabled=False
                )
            )
            
            # Print intermediate results, showing how the user input was enhanced
            print("\n📋 Intermediate Steps:")
            print("-" * 50)
            for item in orchestrator_result.new_items:
                if isinstance(item, MessageOutputItem):
                    text = ItemHelpers.text_message_output(item)
                    if text:
                        print(f"  - Step: {text}")
            
            # Run the synthesizer to get a final coherent response
            synthesizer_result = await Runner.run(
                synthesizer_agent, 
                orchestrator_result.to_input_list(),
                run_config=RunConfig(
                    tracing_disabled=False
                )
            )
            
            # Print final result
            print("\n🎯 Final Result:")
            print("=" * 50)
            print(f"{synthesizer_result.final_output}")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        # Close the HTTP client
        #await http_client.aclose()
        print("\n👋 Thank you for using Enhanced ClickHouse Explorer!")


if __name__ == "__main__":
    asyncio.run(main()) 