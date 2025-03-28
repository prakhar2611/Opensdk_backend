# API Integration Guide

This guide provides information on how to integrate the Agent & Orchestrator API with other systems and automate API interactions.

## API Basics

The Agent & Orchestrator API is a RESTful API that follows standard HTTP conventions:

- GET requests retrieve resources
- POST requests create resources
- PUT requests update resources
- DELETE requests remove resources
- All request and response bodies use JSON format
- Standard HTTP status codes are used (200, 201, 204, 400, 404, 500, etc.)

## Authentication

Currently, the API does not implement authentication. In a production environment, you would want to add authentication (e.g., API keys, OAuth2, JWT) before exposing this API.

## Rate Limiting

The API does not currently implement rate limiting. In a production environment, you should consider adding rate limiting to prevent abuse.

## Integration Options

### 1. Direct API Calls

The simplest way to integrate with the API is by making direct HTTP requests. Here are examples using different tools:

#### cURL

```bash
# Get all agents
curl -X GET "http://localhost:8000/agents/"

# Create a new agent
curl -X POST "http://localhost:8000/agents/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ClickHouse Explorer",
    "system_prompt": "You are an AI assistant that helps users explore ClickHouse database {database}.",
    "additional_prompt": "",
    "selected_tools": ["describe_table", "run_query", "show_tables"],
    "handoff": false,
    "prompt_fields": [
      {
        "name": "database",
        "description": "ClickHouse database name",
        "default_value": "default",
        "required": true
      }
    ]
  }'
```

#### Python Requests

```python
import requests
import json

base_url = "http://localhost:8000"

# Get all agents
response = requests.get(f"{base_url}/agents/")
agents = response.json()

# Create a new agent
agent_data = {
    "name": "ClickHouse Explorer",
    "system_prompt": "You are an AI assistant that helps users explore ClickHouse database {database}.",
    "additional_prompt": "",
    "selected_tools": ["describe_table", "run_query", "show_tables"],
    "handoff": False,
    "prompt_fields": [
        {
            "name": "database",
            "description": "ClickHouse database name",
            "default_value": "default",
            "required": True
        }
    ]
}
response = requests.post(f"{base_url}/agents/", json=agent_data)
new_agent = response.json()
agent_id = new_agent["id"]

# Run an agent
run_data = {
    "user_input": "Show me all tables in the database",
    "prompt_field_values": {
        "database": "default"
    }
}
response = requests.post(f"{base_url}/agents/{agent_id}/run", json=run_data)
result = response.json()
print(result["response"])
```

#### JavaScript / Node.js

```javascript
const axios = require('axios');

const baseUrl = 'http://localhost:8000';

// Get all agents
async function getAllAgents() {
  const response = await axios.get(`${baseUrl}/agents/`);
  return response.data;
}

// Create a new agent
async function createAgent() {
  const agentData = {
    name: 'ClickHouse Explorer',
    system_prompt: 'You are an AI assistant that helps users explore ClickHouse database {database}.',
    additional_prompt: '',
    selected_tools: ['describe_table', 'run_query', 'show_tables'],
    handoff: false,
    prompt_fields: [
      {
        name: 'database',
        description: 'ClickHouse database name',
        default_value: 'default',
        required: true
      }
    ]
  };
  
  const response = await axios.post(`${baseUrl}/agents/`, agentData);
  return response.data;
}

// Run an agent
async function runAgent(agentId) {
  const runData = {
    user_input: 'Show me all tables in the database',
    prompt_field_values: {
      database: 'default'
    }
  };
  
  const response = await axios.post(`${baseUrl}/agents/${agentId}/run`, runData);
  return response.data;
}

// Usage example
async function main() {
  try {
    const newAgent = await createAgent();
    console.log('Created agent:', newAgent);
    
    const result = await runAgent(newAgent.id);
    console.log('Agent response:', result.response);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

main();
```

### 2. Swagger/OpenAPI Client Generation

The API provides Swagger/OpenAPI documentation at `/docs` that can be used to generate client libraries for various programming languages.

1. Visit `http://localhost:8000/docs` in your browser
2. Click the "Download OpenAPI specification" button
3. Use the downloaded specification with tools like Swagger Codegen or OpenAPI Generator to create client libraries

### 3. Automation Using Workflows

You can integrate the API into automation workflows using tools like:

- **GitHub Actions**: Automate agent creation and execution in CI/CD pipelines
- **Zapier/Make**: Connect to thousands of other services without writing code
- **Airflow**: Create data processing pipelines that leverage AI agents
- **Jenkins**: Integrate AI agents into your build process

## Common Integration Patterns

### 1. Batch Processing

```python
import requests
import csv

base_url = "http://localhost:8000"

# Get agent ID
response = requests.get(f"{base_url}/agents/")
agents = response.json()
agent_id = agents[0]["id"]  # Assuming you have at least one agent

# Process a batch of inputs from CSV
with open('queries.csv', 'r') as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    
    results = []
    for row in reader:
        query = row[0]
        database = row[1]
        
        run_data = {
            "user_input": query,
            "prompt_field_values": {
                "database": database
            }
        }
        
        response = requests.post(f"{base_url}/agents/{agent_id}/run", json=run_data)
        result = response.json()
        
        results.append({
            "query": query,
            "database": database,
            "response": result["response"]
        })

# Save results
with open('results.csv', 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=["query", "database", "response"])
    writer.writeheader()
    writer.writerows(results)
```

### 2. Chaining Multiple Agents and Orchestrators

```python
import requests
import json

base_url = "http://localhost:8000"

# Step 1: Get data from first agent
agent1_response = requests.get(f"{base_url}/agents/")
agent1_id = agent1_response.json()[0]["id"]

run_data = {
    "user_input": "List all tables in the database",
    "prompt_field_values": {"database": "default"}
}

agent1_result = requests.post(f"{base_url}/agents/{agent1_id}/run", json=run_data).json()
tables = agent1_result["response"]

# Step 2: Use the output from first agent as input for the orchestrator
orchestrator_response = requests.get(f"{base_url}/orchestrators/")
orchestrator_id = orchestrator_response.json()[0]["id"]

orchestrator_run_data = {
    "user_input": f"Analyze these tables: {tables}",
    "prompt_field_values": {
        "database": "default",
        "time_period": "last 7 days"
    },
    "save_history": True
}

final_result = requests.post(f"{base_url}/orchestrators/{orchestrator_id}/run", json=orchestrator_run_data).json()
print(final_result["response"])
```

## Monitoring and Error Handling

When integrating with the API, implement proper error handling and monitoring:

1. **Handle HTTP Errors**: Check response status codes and handle errors appropriately
2. **Implement Retries**: Use exponential backoff for temporary failures
3. **Logging**: Log API responses for debugging and auditing
4. **Monitoring**: Track API usage, response times, and error rates

## Security Considerations

When deploying in production:

1. **Use HTTPS**: Encrypt all API traffic
2. **Implement Authentication**: Add API keys or OAuth2
3. **Rate Limiting**: Prevent abuse with rate limits
4. **Input Validation**: Validate all inputs to prevent injection attacks
5. **Secrets Management**: Don't hardcode API keys or credentials 