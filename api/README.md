# Agent & Orchestrator API

This API provides a FastAPI-based RESTful interface to the Agent & Orchestrator functionality. It allows you to create, update, delete, and run agents and orchestrators through HTTP endpoints.

## Getting Started

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure your `.env` file is set up with the required environment variables (especially `OPENAI_API_KEY`).

3. Run the API server:
   ```bash
   python api_app.py
   ```

4. Access the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

### Agents

- `GET /agents` - Get all agents
- `GET /agents/{agent_id}` - Get agent by ID
- `POST /agents` - Create a new agent
- `PUT /agents/{agent_id}` - Update an existing agent
- `DELETE /agents/{agent_id}` - Delete an agent
- `GET /agents/tools/available` - Get all available function tools
- `POST /agents/{agent_id}/run` - Run an agent with user input

### Orchestrators

- `GET /orchestrators` - Get all orchestrators
- `GET /orchestrators/{orchestrator_id}` - Get orchestrator by ID
- `POST /orchestrators` - Create a new orchestrator
- `PUT /orchestrators/{orchestrator_id}` - Update an existing orchestrator
- `DELETE /orchestrators/{orchestrator_id}` - Delete an orchestrator
- `POST /orchestrators/{orchestrator_id}/run` - Run an orchestrator with user input
- `GET /orchestrators/{orchestrator_id}/history` - Get conversation history for an orchestrator

### Other Endpoints

- `GET /health` - Check if the API is running
- `GET /` - Get API information

## Examples

### Creating an Agent

```bash
curl -X 'POST' \
  'http://localhost:8000/agents/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
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

### Running an Agent

```bash
curl -X 'POST' \
  'http://localhost:8000/agents/YOUR_AGENT_ID/run' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user_input": "Show me all tables in the database",
  "prompt_field_values": {
    "database": "default"
  }
}'
``` 