from __future__ import annotations

import asyncio
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


"""This example uses a custom provider for some calls to Runner.run(), and direct calls to OpenAI for
others. Steps:
1. Create a custom OpenAI client.
2. Create a ModelProvider that uses the custom client.
3. Use the ModelProvider in calls to Runner.run(), only when we want to use the custom LLM provider.

Note that in this example, we disable tracing under the assumption that you don't have an API key
from platform.openai.com. If you do have one, you can either set the `OPENAI_API_KEY` env var
or call set_tracing_export_api_key() to set a tracing specific key.
"""
client = AsyncOpenAI(
    base_url=BASE_URL, 
    api_key=API_KEY,
    http_client=httpx.AsyncClient(verify=False)  # Bypass SSL certificate verification
)
set_tracing_disabled(disabled=True)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(model=model_name or MODEL_NAME, openai_client=client)



