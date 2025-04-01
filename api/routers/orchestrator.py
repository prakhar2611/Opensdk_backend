from fastapi import APIRouter, HTTPException, Body, Path, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, AsyncIterable
import os
import sys
import asyncio
import json
import uuid
import datetime
import logger
from runner.orchestrator import OrchestratorModelExecutor

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import existing functionality
from models import Orchestrator
from utils import (
    load_orchestrators, save_orchestrators,
    generate_id, delete_orchestrator, load_agents
)
from tools.tools import get_available_tools
from executor import (
    run_orchestrator_by_id, get_conversation_history,
    save_to_conversation_history
)

# Import API models
from api.models import (
    OrchestratorCreate, OrchestratorUpdate, OrchestratorResponse,
    OrchestratorRunRequest, RunResponse
)

router = APIRouter(
    prefix="/orchestrators",
    tags=["Orchestrators"],
    responses={404: {"description": "Not found"}},
)

# Helper functions
def orchestrator_to_response(orch_id: str, orch_data: Dict[str, Any]) -> OrchestratorResponse:
    """Convert orchestrator data to response model"""
    return OrchestratorResponse(
        id=orch_id,
        name=orch_data["name"],
        description=orch_data.get("description", ""),
        agents=orch_data["agents"],
        tools=orch_data["tools"],
        system_prompt=orch_data["system_prompt"]
    )

# GET all orchestrators
@router.get("/", response_model=List[OrchestratorResponse])
async def get_all_orchestrators():
    """Get all orchestrators"""
    orchestrators_data = load_orchestrators()
    return [
        orchestrator_to_response(orch_id, orch_data)
        for orch_id, orch_data in orchestrators_data.items()
    ]

# GET orchestrator by ID
@router.get("/{orchestrator_id}", response_model=OrchestratorResponse)
async def get_orchestrator(orchestrator_id: str = Path(..., description="The ID of the orchestrator to get")):
    """Get a specific orchestrator by ID"""
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    return orchestrator_to_response(orchestrator_id, orchestrators_data[orchestrator_id])

# POST new orchestrator
@router.post("/", response_model=OrchestratorResponse, status_code=201)
async def create_orchestrator(orchestrator: OrchestratorCreate):
    """Create a new orchestrator"""
    orchestrators_data = load_orchestrators()
    agents_data = load_agents()
    
    # Validate that all agent IDs exist
    for agent_id in orchestrator.agents:
        if agent_id not in agents_data:
            raise HTTPException(status_code=400, detail=f"Agent with ID {agent_id} not found")
    
    # Generate ID for new orchestrator
    orchestrator_id = generate_id()
    
    # Create new orchestrator data
    new_orchestrator = Orchestrator(
        id=orchestrator_id,
        name=orchestrator.name,
        description=orchestrator.description,
        agents=orchestrator.agents,
        tools=orchestrator.tools,
        system_prompt=orchestrator.system_prompt
    )
    
    # Add to orchestrators data
    orchestrators_data[orchestrator_id] = new_orchestrator.to_dict()
    
    # Save orchestrators data
    save_orchestrators(orchestrators_data)
    
    return orchestrator_to_response(orchestrator_id, orchestrators_data[orchestrator_id])

# PUT update orchestrator
@router.put("/{orchestrator_id}", response_model=OrchestratorResponse)
async def update_orchestrator(
    orchestrator: OrchestratorUpdate,
    orchestrator_id: str = Path(..., description="The ID of the orchestrator to update")
):
    """Update an existing orchestrator"""
    orchestrators_data = load_orchestrators()
    agents_data = load_agents()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    # Get existing orchestrator data
    orch_data = orchestrators_data[orchestrator_id]
    
    # Update fields if provided
    if orchestrator.name is not None:
        orch_data["name"] = orchestrator.name
    if orchestrator.description is not None:
        orch_data["description"] = orchestrator.description
    if orchestrator.system_prompt is not None:
        orch_data["system_prompt"] = orchestrator.system_prompt
    
    # Validate and update agent IDs if provided
    if orchestrator.agents is not None:
        for agent_id in orchestrator.agents:
            if agent_id not in agents_data:
                raise HTTPException(status_code=400, detail=f"Agent with ID {agent_id} not found")
        orch_data["agents"] = orchestrator.agents
    
    # Update tools if provided
    if orchestrator.tools is not None:
        orch_data["tools"] = orchestrator.tools
    
    # Save updated orchestrators data
    save_orchestrators(orchestrators_data)
    
    return orchestrator_to_response(orchestrator_id, orch_data)

# DELETE orchestrator
@router.delete("/{orchestrator_id}", status_code=204)
async def remove_orchestrator(orchestrator_id: str = Path(..., description="The ID of the orchestrator to delete")):
    """Delete an orchestrator"""
    if not delete_orchestrator(orchestrator_id):
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    return None

# POST run orchestrator
@router.post("/{orchestrator_id}/run", response_model=RunResponse)
async def run_orchestrator(
    run_request: OrchestratorRunRequest,
    orchestrator_id: str = Path(..., description="The ID of the orchestrator to run")
):
    """Run an orchestrator with user input"""
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    try:
        orchestrator_executor = OrchestratorModelExecutor()
        # Run orchestrator
        result = await orchestrator_executor.run_orchestrator_Id(
            orchestratorId=orchestrator_id,
            user_input=run_request.user_input
        )


        #daving the conversation history 
        save_to_conversation_history(orchestrator_id, run_request.user_input, result) 
        
        return RunResponse(
            response=result,
            execution_details={
                "orchestrator_id": orchestrator_id,
                "orchestrator_name": orchestrators_data[orchestrator_id]["name"],
                # "agent_calls": result.get("agent_calls", []),
                # "execution_log": result.get("execution_log", [])
            }
        )
        
    except Exception as e:
        # Re-raise as HTTP exception
        raise HTTPException(status_code=500, detail=f"Error running orchestrator: {str(e)}")

# WebSocket endpoint for streaming orchestrator runs
@router.websocket("/{orchestrator_id}/stream")
async def stream_orchestrator(
    websocket: WebSocket,
    orchestrator_id: str = Path(..., description="The ID of the orchestrator to run")
):
    """Stream an orchestrator run with WebSocket, providing real-time updates"""
    await websocket.accept()
    
    try:
        # Get input from client
        data = await websocket.receive_text()
        run_data = json.loads(data)
        user_input = run_data.get("user_input", "")
        
        orchestrators_data = load_orchestrators()
        
        if orchestrator_id not in orchestrators_data:
            await websocket.send_json({"type": "error", "message": "Orchestrator not found"})
            await websocket.close()
            return
        
        try:
            orchestrator_executor = OrchestratorModelExecutor()
            # Stream orchestrator run
            async for event in orchestrator_executor.stream_orchestrator_run_by_id(
                orchestratorId=orchestrator_id,
                user_input=user_input
            ):
                # Send event to client - use the serializer to ensure JSON compatibility
                event_dict = serialize_event(event)
                await websocket.send_json(event_dict)
            
            # Save the conversation history after streaming is complete
            # Get the final result from the executor
            final_result = orchestrator_executor.get_last_run_result()
            save_to_conversation_history(orchestrator_id, user_input, final_result)
            
            # Send completion event
            await websocket.send_json({"type": "complete", "final_output": final_result})
            
        except Exception as e:
            # Log the error
            logger.error(f"WebSocket Streaming error: {str(e)}")
            # Send error to client
            await websocket.send_json({"type": "error", "message": f"Error running orchestrator: {str(e)}"})
            
    except WebSocketDisconnect:
        # Handle client disconnect
        logger.info(f"WebSocket client disconnected from orchestrator {orchestrator_id}")
    except Exception as e:
        # Log the error
        logger.error(f"WebSocket connection error: {str(e)}")
        # Send error to client if connection is still open
        if websocket.client_state.value != 0:  # Not closed
            await websocket.send_json({"type": "error", "message": f"Error: {str(e)}"})
    finally:
        # Ensure websocket is closed
        if websocket.client_state.value != 0:  # Not closed
            await websocket.close()

# HTTP SSE endpoint for streaming orchestrator runs
@router.post("/{orchestrator_id}/stream-sse")
async def stream_orchestrator_sse(
    run_request: OrchestratorRunRequest,
    orchestrator_id: str = Path(..., description="The ID of the orchestrator to run")
):
    """Stream an orchestrator run using Server-Sent Events (SSE)"""
    
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    async def event_generator() -> AsyncIterable[str]:
        try:
            orchestrator_executor = OrchestratorModelExecutor()
            
            # Stream header
            yield "data: " + json.dumps({"type": "start"}) + "\n\n"
            
            # Stream events
            async for event in orchestrator_executor.stream_orchestrator_run_by_id(
                orchestratorId=orchestrator_id,
                user_input=run_request.user_input
            ):
                # Convert event to serializable dictionary
                event_dict = serialize_event(event)
                
                # Send event
                yield "data: " + json.dumps(event_dict) + "\n\n"
            
            # Save the conversation history after streaming is complete
            # Get the final result from the executor
            final_result = orchestrator_executor.get_last_run_result()
            save_to_conversation_history(orchestrator_id, run_request.user_input, final_result)
            
            # Send completion event
            yield "data: " + json.dumps({"type": "complete", "final_output": final_result}) + "\n\n"
            
        except Exception as e:
            # Send error event
            error_msg = f"Error running orchestrator: {str(e)}"
            logger.error(f"SSE Streaming error: {error_msg}")
            yield "data: " + json.dumps({"type": "error", "message": error_msg}) + "\n\n"
            raise HTTPException(status_code=500, detail=error_msg)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

def serialize_event(event):
    """Convert an event object to a serializable dictionary
    
    Args:
        event: The event object to serialize
        
    Returns:
        A dictionary that can be serialized to JSON
    """
    # Base event dictionary with type
    event_dict = {"type": getattr(event, "type", "unknown_event_type")}
    
    # For each attribute in the event, try to add it to the dictionary in a serializable form
    for attr_name in dir(event):
        # Skip private attributes and methods
        if attr_name.startswith('_') or callable(getattr(event, attr_name)):
            continue
            
        # Get the attribute value
        attr_value = getattr(event, attr_name)
        
        # Handle specific attribute types
        if attr_name == "data":
            # Handle data attribute, which might contain ResponseTextDeltaEvent
            if hasattr(attr_value, "delta"):
                event_dict["data"] = {"delta": attr_value.delta}
            elif hasattr(attr_value, "to_dict"):
                # If it has a to_dict method, use it
                event_dict["data"] = attr_value.to_dict()
            else:
                # For other types, try to get basic attributes
                try:
                    # Try to convert to dict
                    event_dict["data"] = {"type": attr_value.__class__.__name__}
                    
                    # Add common attributes if they exist
                    for data_attr in ["id", "content", "text", "message", "status"]:
                        if hasattr(attr_value, data_attr):
                            event_dict["data"][data_attr] = getattr(attr_value, data_attr)
                except:
                    # If all else fails, just use the string representation
                    event_dict["data"] = str(attr_value)
        
        elif attr_name == "item":
            # Handle item attribute, which might be a RunItem instance
            try:
                # Try to_dict first
                if hasattr(attr_value, "to_dict"):
                    event_dict["item"] = attr_value.to_dict()
                else:
                    # Fall back to manual extraction
                    item_dict = {"type": getattr(attr_value, "type", "unknown")}
                    
                    # Common attributes for all items
                    for item_attr in ["id", "run_id", "tool_name"]:
                        if hasattr(attr_value, item_attr):
                            item_dict[item_attr] = getattr(attr_value, item_attr)
                    
                    # Message specific attributes
                    if hasattr(attr_value, "message"):
                        message = getattr(attr_value, "message")
                        if hasattr(message, "content"):
                            item_dict["message"] = {"content": message.content}
                        else:
                            item_dict["message"] = str(message)
                    
                    # Tool output
                    if hasattr(attr_value, "output"):
                        item_dict["output"] = str(getattr(attr_value, "output"))
                    
                    event_dict["item"] = item_dict
            except Exception as e:
                # If there's an error, log it and use a simpler representation
                logger.debug(f"Error serializing item: {str(e)}")
                event_dict["item"] = {"type": attr_value.__class__.__name__}
        
        elif attr_name == "new_agent":
            # Handle new_agent attribute, which might be an Agent instance
            if attr_value is not None:
                if hasattr(attr_value, "name"):
                    event_dict["new_agent"] = attr_value.name
                else:
                    event_dict["new_agent"] = str(attr_value)
        
        elif attr_name == "timestamp":
            # Handle timestamp attribute
            if isinstance(attr_value, (datetime.datetime, datetime.date)):
                event_dict["timestamp"] = attr_value.isoformat()
            else:
                event_dict["timestamp"] = str(attr_value)
        
        elif attr_name not in ["type"]:  # We already handled "type" 
            # For all other attributes, serialize if possible
            try:
                # Try to directly serialize the value
                json.dumps({attr_name: attr_value})
                event_dict[attr_name] = attr_value
            except (TypeError, OverflowError):
                # If the value is not JSON serializable, convert it to a string
                event_dict[attr_name] = str(attr_value)
    
    return event_dict

# GET conversation history for orchestrator
@router.get("/{orchestrator_id}/history", response_model=List[Dict[str, Any]])
async def get_history(orchestrator_id: str = Path(..., description="The ID of the orchestrator")):
    """Get conversation history for an orchestrator"""
    orchestrators_data = load_orchestrators()
    
    if orchestrator_id not in orchestrators_data:
        raise HTTPException(status_code=404, detail="Orchestrator not found")
    
    return get_conversation_history(orchestrator_id) 