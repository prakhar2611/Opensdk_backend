# AI Agent Framework: Technical Documentation

## Core Components

### Agent Class

The `Agent` class is the fundamental building block of the framework. Each agent is a specialized AI entity with specific capabilities and instructions.

```python
from agents import Agent

my_agent = Agent(
    name="MyAgent",
    instructions="Your role-specific instructions here",
    tools=[list_of_tools],  # Optional
    hooks=CustomAgentHooks()  # Optional
)
```

#### Parameters:
- `name`: Unique identifier for the agent
- `instructions`: Detailed instructions that define the agent's role and capabilities
- `tools`: List of function tools or agent tools the agent can use
- `hooks`: Custom hooks for lifecycle events (optional)
- `handoff_description`: Description for when this agent is used as a tool (optional)

### Runner

The `Runner` class executes agents and handles their interactions.

```python
from agents import Runner, RunConfig

result = await Runner.run(
    agent,
    input_data,
    run_config=RunConfig(tracing_disabled=False)
)
```

#### Parameters:
- `agent`: The agent to execute
- `input_data`: Input for the agent (string or list of items)
- `run_config`: Configuration options

#### Return Value:
- `AgentOutput` object containing:
  - `final_output`: The agent's final response
  - `new_items`: All items created during execution
  - `to_input_list()`: Method to convert output to input for another agent

### Trace System

The trace system provides visibility into agent execution.

```python
from agents import trace

with trace("My Trace Session"):
    # Agent execution code here
    result = await Runner.run(agent, input_data)
```

## Agent Tools

### Function Tools

Functions can be registered as tools using the `@function_tool` decorator.

```python
from agents import function_tool
from typing import List, Dict

@function_tool
def query_database(query: str) -> List[Dict]:
    """
    Execute SQL query against the database.
    
    Args:
        query: SQL query to execute
        
    Returns:
        List of records as dictionaries
    """
    # Implementation
    return results
```

### Registering Agents as Tools

Agents can be used as tools by other agents.

```python
# Create specialist agent
specialist_agent = Agent(
    name="SpecialistAgent",
    instructions="You are a specialist that...",
    handoff_description="A specialized agent for handling X tasks"
)

# Register as tool in orchestrator
orchestrator_agent = Agent(
    name="OrchestratorAgent",
    instructions="You coordinate between specialists...",
    tools=[
        specialist_agent.as_tool(
            tool_name="use_specialist",
            tool_description="Use this specialist agent when..."
        )
    ]
)
```

## Agent Lifecycle Hooks

Custom hooks allow monitoring agent execution.

```python
from agents import AgentHooks, RunContextWrapper, Agent, Tool

class CustomAgentHooks(AgentHooks):
    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        print(f"Agent {agent.name} started")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        print(f"Agent {agent.name} ended with output: {output}")

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        print(f"Agent {source.name} handed off to {agent.name}")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        print(f"Agent {agent.name} started tool {tool.name}")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        print(f"Agent {agent.name} ended tool {tool.name} with result: {result}")
```

## Specialized Agent Implementations

### Creating the Orchestrator Agent

```python
def create_orchestrator_agent():
    """
    Creates and returns the orchestrator agent
    """
    # Create specialized agents to use as tools
    clickhouse_agent = create_clickhouse_agent()
    analyst_agent = create_analyst_agent()
    visualization_agent = create_visualization_agent()
    
    # Create the orchestrator
    orchestrator_agent = Agent(
        name="Orchestrator Agent",
        instructions="""
        You are an intelligent orchestrator that coordinates between specialized agents.
        Based on the user's request, determine which agent is best suited to handle it.
        
        Workflow:
        1. Analyze user request
        2. Choose appropriate specialist(s)
        3. Coordinate responses
        """,
        tools=[
            clickhouse_agent.as_tool(
                tool_name="use_clickhouse_agent",
                tool_description="Use for database operations"
            ),
            analyst_agent.as_tool(
                tool_name="use_analyst_agent",
                tool_description="Use for data analysis"
            ),
            visualization_agent.as_tool(
                tool_name="use_visualization_agent",
                tool_description="Use for data visualization"
            )
        ],
        hooks=CustomAgentHooks(display_name="Orchestrator")
    )
    
    return orchestrator_agent
```

### Database Agent Implementation

```python
def create_clickhouse_agent(database=None, tables=None):
    """
    Create a ClickHouse database agent
    """
    return Agent(
        name="ClickHouse Agent",
        instructions="""
        You are a database expert that helps users interact with ClickHouse.
        You can execute queries, explore schema, and retrieve data.
        """,
        tools=[
            show_databases,
            show_tables,
            describe_table,
            execute_query,
            # More database-specific tools
        ]
    )
```

## External Integrations

### Database Connection

```python
from clickhouse_connect.driver.client import Client
import clickhouse_connect
import os

def get_clickhouse_client() -> Client:
    """Get a ClickHouse client using environment variables"""
    host = os.environ.get("CLICKHOUSE_HOST", "localhost")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
    username = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD", "")
    database = os.environ.get("CLICKHOUSE_DATABASE", "default")
    
    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database
    )
    
    return client
```

### OpenAI Configuration

```python
from agents.models._openai_shared import set_default_openai_client
from openai import AsyncOpenAI
import httpx
import os

def setup_openai_client():
    # Create a custom transport with SSL verification disabled for development
    transport = httpx.AsyncHTTPTransport(
        verify=False,
        http2=True
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
    
    return http_client
```

## Message Handling

### Input/Output Types

The framework uses structured message types:

- `MessageOutputItem`: Represents a message from an agent
- `ContentItem`: Base class for all content types
- `ErrorItem`: Represents errors during execution

```python
from agents import ItemHelpers, MessageOutputItem

# Extract text from a message output item
text = ItemHelpers.text_message_output(message_item)

# Convert agent output to input for another agent
input_for_next_agent = agent_result.to_input_list()
```

## Application Patterns

### Enhanced Context Pattern

```python
# Enhanced orchestrator that modifies user input
def create_enhanced_orchestrator_agent():
    """
    Creates an orchestrator that enhances user queries before passing to specialists
    """
    clickhouse_agent = create_clickhouse_agent()
    
    orchestrator_agent = Agent(
        name="Enhanced Orchestrator",
        instructions="""
        You enhance user queries with additional context before delegating.
        For database queries:
        1. Analyze the user query
        2. Add specific details or constraints that would improve results
        3. Pass the enhanced query to the database agent
        """,
        tools=[
            clickhouse_agent.as_tool(
                tool_name="use_enhanced_clickhouse",
                tool_description="Use with enhanced context"
            )
        ]
    )
    
    return orchestrator_agent
```

### Agents-as-Tools Pattern

```python
spanish_agent = Agent(
    name="spanish_agent",
    instructions="You translate to Spanish",
    handoff_description="English to Spanish translator"
)

french_agent = Agent(
    name="french_agent", 
    instructions="You translate to French",
    handoff_description="English to French translator"
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions="You route translation requests",
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate to Spanish"
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate to French"
        )
    ]
)
```

## Best Practices

### Agent Design

1. **Clear Instructions**
   - Be specific about the agent's role
   - Define boundaries and capabilities
   - Specify input/output expectations

2. **Tool Organization**
   - Group related functionality
   - Name tools clearly and consistently
   - Provide detailed descriptions

3. **Error Handling**
   - Implement robust error catching
   - Design graceful degradation paths
   - Log issues in the trace system

### Performance Optimization

1. **Minimize Agent Handoffs**
   - Each handoff adds latency
   - Batch related operations where possible
   - Consider specialized agents for high-frequency paths

2. **Context Management**
   - Pass only necessary context
   - Structure data for efficient processing
   - Trim large payloads

## Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install agents langchain autogen openai clickhouse-connect python-dotenv

# Environment variables in .env file
OPENAI_API_KEY=your_api_key
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=default
```

## Debugging & Monitoring

### Trace Analysis

Access trace events to debug agent execution:

```python
with trace("Debug Session") as session:
    result = await Runner.run(agent, input_data)
    
    # Access trace events
    for event in session.events:
        print(f"Event: {event.type}, Agent: {event.agent_name}")
```

### Performance Monitoring

Track agent execution times:

```python
import time

class PerformanceHooks(AgentHooks):
    def __init__(self):
        self.start_times = {}
        
    async def on_start(self, context, agent):
        self.start_times[agent.name] = time.time()
        
    async def on_end(self, context, agent, output):
        duration = time.time() - self.start_times.get(agent.name, 0)
        print(f"Agent {agent.name} took {duration:.2f} seconds")
```

## Common Troubleshooting

1. **SSL Verification Issues**
   - Use `setup_ssl_bypass()` function for development
   - Configure proper certificates for production

2. **API Key Issues**
   - Verify `.env` file loading correctly
   - Check environment variables are accessible

3. **Agent Timeout Issues**
   - Configure timeout in RunConfig
   - Split complex tasks into smaller units

4. **Memory Management**
   - Avoid storing large datasets in context
   - Use external storage for large results

## Framework Extension

### Custom Agent Types

```python
class SpecializedAgent(Agent):
    """Custom agent with additional capabilities"""
    
    def __init__(self, name, instructions, domain_knowledge=None, **kwargs):
        super().__init__(name, instructions, **kwargs)
        self.domain_knowledge = domain_knowledge
        
    async def process_with_knowledge(self, input_data):
        """Process using specialized domain knowledge"""
        # Implementation
        return results
```

### New Tool Types

```python
class ApiTool(Tool):
    """Tool for API integration"""
    
    def __init__(self, name, description, api_url, method="GET"):
        super().__init__(name, description)
        self.api_url = api_url
        self.method = method
        
    async def execute(self, params):
        """Execute API call"""
        # Implementation
        return response
``` 