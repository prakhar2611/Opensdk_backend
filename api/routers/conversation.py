from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Dict, Any, Optional
import os
import json
import glob
from datetime import datetime, date

# Create router
router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
    responses={404: {"description": "Not found"}},
)

def load_conversation_file(file_path: str) -> List[Dict[str, Any]]:
    """Load conversation history from a file"""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []
    except FileNotFoundError:
        return []

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_conversations():
    """Get a list of all available conversations"""
    conversations_dir = "data/conversations"
    
    # Ensure the directory exists
    if not os.path.exists(conversations_dir):
        return []
    
    # Find all JSON files in the conversations directory
    json_files = glob.glob(os.path.join(conversations_dir, "*.json"))
    
    # Create a list of conversation summaries
    conversation_list = []
    for file_path in json_files:
        conversation_id = os.path.basename(file_path).replace(".json", "")
        history = load_conversation_file(file_path)
        
        # Count messages
        message_count = len(history)
        
        # Get the latest timestamp
        latest_timestamp = None
        if history:
            # Sort by timestamp (newest first)
            sorted_history = sorted(
                history, 
                key=lambda x: x.get("timestamp", ""), 
                reverse=True
            )
            latest_timestamp = sorted_history[0].get("timestamp", None)
        
        conversation_list.append({
            "id": conversation_id,
            "message_count": message_count,
            "latest_timestamp": latest_timestamp
        })
    
    return conversation_list

@router.get("/{conversation_id}", response_model=List[Dict[str, Any]])
async def get_conversation_by_id(
    conversation_id: str = Path(..., description="The ID of the conversation to get"),
    limit: Optional[int] = Query(None, description="Limit the number of messages"),
    offset: Optional[int] = Query(None, description="Offset for pagination"),
    sort: Optional[str] = Query("desc", description="Sort order (asc or desc)"),
    start_date: Optional[date] = Query(None, description="Filter messages after this date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter messages before this date (inclusive)")
):
    """Get conversation history by ID with optional filtering and pagination"""
    file_path = f"data/conversations/{conversation_id}.json"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    history = load_conversation_file(file_path)
    
    # Apply date filtering if specified
    if start_date or end_date:
        filtered_history = []
        for message in history:
            timestamp_str = message.get("timestamp", "")
            if not timestamp_str:
                continue
                
            try:
                # Parse timestamp string to datetime
                message_date = datetime.fromisoformat(timestamp_str).date()
                
                # Apply date range filtering
                include_message = True
                if start_date and message_date < start_date:
                    include_message = False
                if end_date and message_date > end_date:
                    include_message = False
                    
                if include_message:
                    filtered_history.append(message)
            except (ValueError, TypeError):
                # Skip messages with invalid timestamps
                continue
                
        history = filtered_history
    
    # Sort by timestamp
    if sort.lower() == "asc":
        history.sort(key=lambda x: x.get("timestamp", ""))
    else:
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Apply pagination if specified
    if offset is not None:
        history = history[offset:]
    
    if limit is not None:
        history = history[:limit]
    
    return history 

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_conversations(
    query: str = Query(..., description="Search term to look for in messages"),
    limit: Optional[int] = Query(20, description="Maximum number of results to return")
):
    """Search all conversations for messages containing the specified query"""
    conversations_dir = "data/conversations"
    
    # Ensure the directory exists
    if not os.path.exists(conversations_dir):
        return []
    
    # Find all JSON files in the conversations directory
    json_files = glob.glob(os.path.join(conversations_dir, "*.json"))
    
    # Search through all conversations
    results = []
    for file_path in json_files:
        conversation_id = os.path.basename(file_path).replace(".json", "")
        history = load_conversation_file(file_path)
        
        for message in history:
            # Search in user messages
            user_message = message.get("user", "")
            if query.lower() in user_message.lower():
                result = {**message, "conversation_id": conversation_id, "match_type": "user"}
                results.append(result)
                
                # Break early if we've hit the limit
                if len(results) >= limit:
                    return results
            
            # Search in assistant responses
            response = message.get("response", "")
            if query.lower() in response.lower():
                result = {**message, "conversation_id": conversation_id, "match_type": "response"}
                results.append(result)
                
                # Break early if we've hit the limit
                if len(results) >= limit:
                    return results
    
    return results 

@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str = Path(..., description="The ID of the conversation to delete")
):
    """Delete a conversation history file"""
    file_path = f"data/conversations/{conversation_id}.json"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    try:
        os.remove(file_path)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@router.delete("/{conversation_id}/messages", status_code=204)
async def clear_conversation(
    conversation_id: str = Path(..., description="The ID of the conversation to clear")
):
    """Clear all messages from a conversation but keep the file"""
    file_path = f"data/conversations/{conversation_id}.json"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    try:
        # Write an empty array to the file
        with open(file_path, "w") as f:
            json.dump([], f)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}") 