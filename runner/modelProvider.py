import os
from openai import AsyncOpenAI
import httpx

from agents import (
    Agent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    function_tool,
    set_tracing_disabled,
)

BASE_URL = os.getenv("USER_BASE_URL") or "https://api.anthropic.com/v1/"
API_KEY = os.getenv("USER_API_KEY") or ""
MODEL_NAME = os.getenv("USER_MODEL") or "claude-3-7-sonnet-20250219"

if not BASE_URL or not API_KEY or not MODEL_NAME:
    raise ValueError(
        "Please set EXAMPLE_BASE_URL, EXAMPLE_API_KEY, EXAMPLE_MODEL_NAME via env var or code."
    )

client = AsyncOpenAI(
    base_url=BASE_URL, 
    api_key=API_KEY,
    http_client=httpx.AsyncClient(verify=False)  # Bypass SSL certificate verification
)
set_tracing_disabled(disabled=True)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(model=model_name or MODEL_NAME, openai_client=client)

