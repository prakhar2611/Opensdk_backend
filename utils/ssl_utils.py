import os
import ssl
import httpx
from openai import AsyncOpenAI
from agents.models._openai_shared import set_default_openai_client

def setup_ssl_bypass():
    """
    Sets up SSL bypass for the OpenAI client and returns the HTTP client.
    """
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