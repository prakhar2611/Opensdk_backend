import asyncio
import os
from dotenv import load_dotenv

from agents import ItemHelpers, MessageOutputItem, Runner, trace, RunConfig
from src.utils.ssl_utils import setup_ssl_bypass
from src.utils.clickhouse_utils import check_db_connectivity
from experiments.agents import (
    create_clickhouse_agent,
    create_user_input_agent,
    create_orchestrator_agent,
    create_synthesizer_agent
)

# Load environment variables from .env file
load_dotenv()

async def main():
    """
    Main function to run the application
    """
    # Set up SSL bypass
    http_client = setup_ssl_bypass()
    
    try:
        print("🔍 ClickHouse Explorer & Analyzer 🔍")
        print("=" * 40)
        
        # Check database connectivity before proceeding
        if not check_db_connectivity():
            print("❌ Cannot connect to ClickHouse database. Please check your connection settings.")
            return
        
        # Run the orchestration in a single trace
        with trace("ClickHouse Explorer Session"):
            # Get initial user query
            user_query = input("\n🤔 What would you like to do with ClickHouse? (You can query data and analyze it for outliers and correlations) ")
            
            # Create agents
            orchestrator_agent = create_orchestrator_agent()
            #synthesizer_agent = create_synthesizer_agent()
            
            # Run the orchestrator
            print("\n🔄 Processing your request...\n")
            orchestrator_result = await Runner.run(
                orchestrator_agent, 
                user_query,
                run_config=RunConfig(
                    tracing_disabled=False
                )
            )
            
            # Print intermediate results for debugging
            print("\n📋 Intermediate Steps:")
            print("-" * 40)
            for item in orchestrator_result.new_items:
                if isinstance(item, MessageOutputItem):
                    text = ItemHelpers.text_message_output(item)
                    if text:
                        print(f"  - Step: {text}")
            
            # Run the synthesizer to get a final coherent response currently removing 
            # synthesizer_result = await Runner.run(
            #     synthesizer_agent, 
            #     orchestrator_result.to_input_list(),
            #     run_config=RunConfig(
            #         tracing_disabled=False
            #     )
            # )
            
            # Print final result
            print("\n🎯 Final Result:")
            print("=" * 40)
            print(f"{orchestrator_result.final_output}")
            print("=" * 40)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        # Close the HTTP client
        await http_client.aclose()
        print("\n👋 Thank you for using ClickHouse Explorer & Analyzer!")


if __name__ == "__main__":
    asyncio.run(main()) 