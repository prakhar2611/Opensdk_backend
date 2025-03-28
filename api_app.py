import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY not found in environment variables.")
    print("You must set this environment variable to use the agent and orchestrator functionality.")

def start_api():
    """Start the FastAPI application with uvicorn server"""
    # Import the FastAPI app
    from api.main import app
    
    # Run the server with uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload for development
    )

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Start the API server
    start_api() 