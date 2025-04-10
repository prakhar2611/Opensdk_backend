from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import os
import asyncio
from typing import AsyncGenerator

router = APIRouter(
    prefix="/streaming",
    tags=["streaming"],
    responses={404: {"description": "Not found"}},
)

async def stream_data_generator() -> AsyncGenerator[str, None]:
    """
    Generator that reads the data file line by line and yields each line
    with a small delay to simulate streaming.
    """
    data_file_path = os.path.join("data", "streaming_data_2.txt")
    
    try:
        with open(data_file_path, "r") as file:
            for line in file:
                # Add a small delay to simulate real-time streaming
                await asyncio.sleep(0.1)
                yield f"{line}"
    except Exception as e:
        yield f"data: {{'error': '{str(e)}'}}\n\n"

@router.get("/demo-sse-streaming")
async def demo_sse_streaming(request: Request) -> StreamingResponse:
    """
    Stream the content of data/streaming_data_2.txt as Server-Sent Events.
    """
    return StreamingResponse(
        stream_data_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        }
    ) 