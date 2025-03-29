import asyncio
import random
import os
import ssl
import httpx
import sys
from typing import Any, List, Dict
from dotenv import load_dotenv
import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError

from pydantic import BaseModel

from agents import Agent, AgentHooks, RunContextWrapper, Runner, Tool, function_tool, RunConfig, trace
from agents.models._openai_shared import set_default_openai_client
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()

# ClickHouse connection setup
def get_clickhouse_client():
    """Get a ClickHouse client using environment variables"""
    host = os.environ.get("CLICKHOUSE_HOST", "localhost")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8123"))  # HTTP interface port is 8123
    username = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD", "")
    database = os.environ.get("CLICKHOUSE_DATABASE", "default")
    
    # Print connection details for debugging
    print(f"[DEBUG] Connecting to ClickHouse: {host}:{port}, db={database}, user={username}")
    
    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database
    )
    
    return client

# Function to check database connectivity
def check_db_connectivity():
    """Check if ClickHouse database is reachable and connection settings are correct"""
    try:
        # Get connection details for logging
        host = os.environ.get("CLICKHOUSE_HOST", "localhost")
        port = os.environ.get("CLICKHOUSE_PORT", "8123")
        username = os.environ.get("CLICKHOUSE_USER", "default")
        database = os.environ.get("CLICKHOUSE_DATABASE", "default")
        
        print(f"Checking connection to ClickHouse at {host}:{port}...")
        client = get_clickhouse_client()
        
        # Run a simple query to verify connection
        result = client.query("SELECT 1")
        if result.result_rows and result.result_rows[0][0] == 1:
            print(f"✅ Successfully connected to ClickHouse database at {host}:{port}")
            print(f"   Database: {database}")
            print(f"   Username: {username}")
            return True
    except ClickHouseError as e:
        print(f"❌ Failed to connect to ClickHouse: {str(e)}")
        print(f"Connection details:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Database: {database}")
        print(f"   Username: {username}")
        print(f"Please check your connection settings in the .env file.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error when connecting to ClickHouse: {str(e)}")
        return False

# Set up SSL bypass
def setup_ssl_bypass():
    # Create a custom transport with SSL verification disabled
    transport = httpx.AsyncHTTPTransport(
        verify=False,  # Disable SSL verification
        http2=True     # Enable HTTP/2 for better performance
    )
    
    # Create httpx client with the custom transport
    http_client = httpx.AsyncClient(transport=transport)
    
    # Get OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Initialize OpenAI client with the custom client
    openai_client = AsyncOpenAI(
        api_key=api_key,
        http_client=http_client
    )
    
    # Set the client as the default
    set_default_openai_client(openai_client)
    
    # Disable SSL verification globally
    ssl._create_default_https_context = ssl._create_unverified_context
    
    return http_client


class CustomAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        print(f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended with output {output}"
        )

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {source.name} handed off to {agent.name}"
        )

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started tool {tool.name}"
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended tool {tool.name} with result {result}"
        )


###

# Original tools
@function_tool
def random_number(max: int) -> int:
    """
    Generate a random number up to the provided maximum.
    """
    return random.randint(0, max)


@function_tool
def multiply_by_two(x: int) -> int:
    """Simple multiplication by two."""
    return x * 2


# ClickHouse database tools
@function_tool
def show_databases() -> List[str]:
    """
    Show all databases in the ClickHouse server.
    Returns a list of database names.
    """
    try:
        client = get_clickhouse_client()
        result = client.query("SHOW DATABASES")
        databases = [row[0] for row in result.result_rows]
        return databases
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
def show_tables(database: str = None) -> List[str]:
    """
    Show all tables in the specified ClickHouse database.
    If no database is specified, uses the default database from connection.
    Returns a list of table names.
    """
    try:
        client = get_clickhouse_client()
        if database:
            result = client.query(f"SHOW TABLES FROM {database}")
        else:
            result = client.query("SHOW TABLES")
        tables = [row[0] for row in result.result_rows]
        return tables
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
def describe_table(table: str, database: str = None) -> List[Dict[str, str]]:
    """
    Describe the structure of a specified table.
    If no database is specified, uses the default database from connection.
    Returns the table structure with column names and types.
    """
    try:
        client = get_clickhouse_client()
        if database:
            query = f"DESCRIBE TABLE {database}.{table}"
        else:
            query = f"DESCRIBE TABLE {table}"
        
        result = client.query(query)
        
        # Convert to a list of dictionaries for better readability
        columns = []
        for row in result.result_rows:
            columns.append({
                "name": row[0],
                "type": row[1],
                "default_type": row[2],
                "default_expression": row[3]
            })
        
        return columns
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
def run_query(query: str) -> List[Dict]:
    """
    Run a custom SQL query on ClickHouse.
    Returns the query results as a list of dictionaries.
    Use with caution, as this allows arbitrary SQL execution.
    """
    try:
        client = get_clickhouse_client()
        result = client.query(query)
        
        # Convert to list of dictionaries for better readability
        rows = []
        column_names = [col[0] for col in result.column_names]
        
        for row in result.result_rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = row[i]
            rows.append(row_dict)
        
        return rows
    except Exception as e:
        return f"Error: {str(e)}"


class FinalResult(BaseModel):
    number: int


multiply_agent = Agent(
    name="Multiply Agent",
    instructions="Multiply the number by 2 and then return the final result.",
    tools=[multiply_by_two],
    output_type=FinalResult,
    hooks=CustomAgentHooks(display_name="Multiply Agent"),
)

start_agent = Agent(
    name="Start Agent",
    instructions="Generate a random number. If it's even, stop. If it's odd, hand off to the multiply agent.",
    tools=[random_number],
    output_type=FinalResult,
    handoffs=[multiply_agent],
    hooks=CustomAgentHooks(display_name="Start Agent"),
)

# Create a ClickHouse database agent with the new tools
clickhouse_agent = Agent(
    name="ClickHouse Agent",
    instructions="""
    You are a ClickHouse database expert.
    You can help users explore and query ClickHouse databases.
    Available tools:
    - show_databases: List all databases
    - show_tables: List tables in a database
    - describe_table: Show structure of a table
    - run_query: Run a SQL query
    
    Only use the tools provided. Be careful with run_query and make sure 
    the query is valid ClickHouse SQL before executing it.
    """,
    tools=[show_databases, show_tables, describe_table, run_query],
    hooks=CustomAgentHooks(display_name="ClickHouse Agent"),
)


async def main() -> None:
    # Set up SSL bypass
    http_client = setup_ssl_bypass()
    
    try:
        with trace("Joke workflow"):
            # Ask user which agent to run
            print("Choose an agent to run:")
            print("1. Random number generator agent")
            print("2. ClickHouse database agent")
            choice = input("Enter your choice (1 or 2): ")
            
            if choice == "1":
                user_input = input("Enter a max number: ")
                await Runner.run(
                    start_agent,
                    input=f"Generate a random number between 0 and {user_input}.",
                    run_config = RunConfig(
                        tracing_disabled = False
                    )
                )
            elif choice == "2":
                # Check database connectivity before proceeding
                if not check_db_connectivity():
                    print("❌ Cannot connect to ClickHouse database. Agent will not be started.")
                    return
                
                user_input = input("What would you like to do with ClickHouse? ")
                await Runner.run(
                    clickhouse_agent,
                    input=user_input,
                    run_config = RunConfig(
                        tracing_disabled = False
                    )
                )
            else:
                print("Invalid choice. Please enter 1 or 2.")

            print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the HTTP client
        await http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
"""
$ python examples/basic/agent_lifecycle_example.py

Enter a max number: 250
### (Start Agent) 1: Agent Start Agent started
### (Start Agent) 2: Agent Start Agent started tool random_number
### (Start Agent) 3: Agent Start Agent ended tool random_number with result 37
### (Start Agent) 4: Agent Start Agent started
### (Start Agent) 5: Agent Start Agent handed off to Multiply Agent
### (Multiply Agent) 1: Agent Multiply Agent started
### (Multiply Agent) 2: Agent Multiply Agent started tool multiply_by_two
### (Multiply Agent) 3: Agent Multiply Agent ended tool multiply_by_two with result 74
### (Multiply Agent) 4: Agent Multiply Agent started
### (Multiply Agent) 5: Agent Multiply Agent ended with output number=74
Done!
"""
