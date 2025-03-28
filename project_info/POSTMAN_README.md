# Agent & Orchestrator API - Postman Collection

This directory contains a Postman collection and environment that can be used to interact with the Agent & Orchestrator API.

## Setup Instructions

1. Install [Postman](https://www.postman.com/downloads/)

2. Import the collection:
   - Open Postman
   - Click on "Import" in the top left corner
   - Drag and drop the `agent_orchestrator_api_postman_collection.json` file or browse to select it
   - Click "Import"

3. Import the environment:
   - In Postman, click on "Import" again
   - Drag and drop the `agent_orchestrator_api_environment.json` file or browse to select it
   - Click "Import"
   - In the top-right environment dropdown, select "Agent & Orchestrator API - Local"

Alternatively, you can manually set up the environment:
   - Click on "Environments" in the sidebar
   - Click "Create New" or "+" button 
   - Name the environment (e.g., "Agent & Orchestrator API - Local")
   - Add the following variables:
     - `baseUrl`: http://localhost:8000 (or your server's base URL)
     - `agentId`: (leave empty for now)
     - `orchestratorId`: (leave empty for now)
   - Click "Save"
   - In the top-right environment dropdown, select your newly created environment

## Using the Collection

The collection is organized into three folders:

1. **General** - Basic API operations
   - Health Check - Verify the API is running
   - API Info - Get general API information

2. **Agents** - Agent-related operations
   - Get All Agents - Fetch all available agents
   - Get Agent by ID - Fetch a specific agent
   - Create Agent - Create a new agent
   - Update Agent - Modify an existing agent
   - Delete Agent - Remove an agent
   - Get Available Tools - Get all available function tools
   - Run Agent - Execute an agent with input

3. **Orchestrators** - Orchestrator-related operations
   - Get All Orchestrators - Fetch all available orchestrators
   - Get Orchestrator by ID - Fetch a specific orchestrator
   - Create Orchestrator - Create a new orchestrator
   - Update Orchestrator - Modify an existing orchestrator
   - Delete Orchestrator - Remove an orchestrator
   - Run Orchestrator - Execute an orchestrator with input
   - Get Orchestrator History - Get conversation history

## Workflow Examples

### Working with Agents

1. Start the API server:
   ```
   python api_app.py
   ```

2. Use the "Get All Agents" request to see if any agents exist

3. Create a new agent:
   - Use the "Create Agent" request
   - The response will include the new agent's ID
   - Set the `agentId` environment variable to this ID:
     - Click the eye icon in the top right to view environment variables
     - Click "Edit" next to your environment
     - Update the `agentId` value
     - Click "Save"

4. Run the agent:
   - Use the "Run Agent" request
   - Modify the request body with your specific input and prompt field values

### Working with Orchestrators

1. Create agents first (if needed)

2. Create an orchestrator:
   - Use the "Create Orchestrator" request
   - Update the JSON body with agent IDs from your created agents
   - The response will include the new orchestrator's ID
   - Set the `orchestratorId` environment variable to this ID:
     - Click the eye icon in the top right to view environment variables
     - Click "Edit" next to your environment
     - Update the `orchestratorId` value
     - Click "Save"

3. Run the orchestrator:
   - Use the "Run Orchestrator" request
   - Modify the request body with your specific input and prompt field values

4. View the conversation history:
   - Use the "Get Orchestrator History" request

## Testing the Collection

Each request includes a description of what it does. You can use the Postman Runner to run a sequence of requests to test the full API workflow:

1. Click on the collection name
2. Click "Run" button
3. Select the requests you want to run in order
4. Click "Run [Collection Name]"

## Troubleshooting

- If you get a 404 error, check that your API server is running
- If you get a 400 error, check your request body format
- For any other issues, check the API server logs

## Automatically Setting Environment Variables

The collection includes scripts to automatically set environment variables. For example, when you create a new agent, the ID from the response will be automatically saved to the `agentId` environment variable. These scripts make it easier to chain requests together. 