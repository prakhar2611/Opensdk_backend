from typing import Dict, List, Any
import sys
import os

# Add parent directory to sys.path to access experiments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ClickHouse functions from experiments
from tools.clickhouse_agent import describe_table, run_query
from tools.visualization_agent import visualize_data
# Define default function tools
DEFAULT_FUNCTION_TOOLS = [
    {
        "name": "search_web",
        "description": "Search the web for information on a given topic",
        "parameters": {
            "query": {
                "type": "string",
                "description": "The search query"
            }
        }
    },
    {
        "name": "fetch_data",
        "description": "Fetch data from a specified API endpoint",
        "parameters": {
            "url": {
                "type": "string",
                "description": "The API endpoint URL"
            },
            "params": {
                "type": "object",
                "description": "Query parameters for the API request"
            }
        }
    },
    {
        "name": "read_file",
        "description": "Read a file from the file system",
        "parameters": {
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            }
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "parameters": {
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        }
    },
    {
        "name": "run_code",
        "description": "Run a code snippet",
        "parameters": {
            "language": {
                "type": "string",
                "description": "Programming language of the code snippet"
            },
            "code": {
                "type": "string",
                "description": "Code to execute"
            }
        }
    },
    {
        "name": "summarize_text",
        "description": "Summarize a piece of text",
        "parameters": {
            "text": {
                "type": "string",
                "description": "Text to summarize"
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum length of the summary"
            }
        }
    },
    {
        "name": "translate_text",
        "description": "Translate text from one language to another",
        "parameters": {
            "text": {
                "type": "string",
                "description": "Text to translate"
            },
            "source_language": {
                "type": "string",
                "description": "Source language code"
            },
            "target_language": {
                "type": "string",
                "description": "Target language code"
            }
        }
    },
    {
        "name": "generate_image",
        "description": "Generate an image based on a text prompt",
        "parameters": {
            "prompt": {
                "type": "string",
                "description": "Text prompt describing the desired image"
            },
            "size": {
                "type": "string",
                "description": "Size of the generated image (e.g., '512x512')"
            }
        }
    },
    {
        "name": "describe_table",
        "description": "Describe the structure of a specified ClickHouse table",
        "parameters": {
            "table": {
                "type": "string",
                "description": "The name of the table to describe"
            },
            "database": {
                "type": "string",
                "description": "Optional database name. If not provided, uses the default database",
                "required": False
            }
        },
        "function": describe_table
    },
    {
        "name": "run_query",
        "description": "Run a custom SQL query on ClickHouse",
        "parameters": {
            "query": {
                "type": "string",
                "description": "The SQL query to execute on ClickHouse"
            },
            "database": {
                "type": "string",
                "description": "Optional database name. If not provided, uses the default database",
                "required": False
            }
        },
        "function": run_query
    },
    {
        "name": "get_html",
        "description": "Generate the html code for the given query",
        "parameters": {
            "data": {
                "type": "json",
                "description": "json data from the clickhouse query"
            }
        },
        "function": visualize_data
    }
]

def get_available_tools() -> List[Dict[str, Any]]:
    """
    Get the list of available function tools.
    
    Returns:
        List[Dict[str, Any]]: List of function tools
    """
    # Create a copy of tools without function references to ensure it can be serialized by Pydantic
    serializable_tools = []
    for tool in DEFAULT_FUNCTION_TOOLS:
        # Create a copy of the tool without the 'function' key
        serializable_tool = {k: v for k, v in tool.items() if k != 'function'}
        serializable_tools.append(serializable_tool)
    
    return serializable_tools

def get_tool_by_name(name: str) -> Dict[str, Any]:
    """
    Get a tool by its name.
    
    Args:
        name (str): Name of the tool
        
    Returns:
        Dict[str, Any]: Tool definition
    """
    for tool in DEFAULT_FUNCTION_TOOLS:
        if tool["name"] == name:
            return tool
    return None


# # Additional ClickHouse tools
# CLICKHOUSE_TOOLS = [
#     {
#         "name": "show_databases",
#         "description": "Show all databases in the ClickHouse server",
#         "parameters": {}
#     },
#     {
#         "name": "show_tables", 
#         "description": "Show all tables in the specified ClickHouse database",
#         "parameters": {
#             "database": {
#                 "type": "string",
#                 "description": "Database name (optional)"
#             }
#         }
#     },
#     {
#         "name": "describe_table",
#         "description": "Describe the structure of a specified table",
#         "parameters": {
#             "table": {
#                 "type": "string", 
#                 "description": "Name of the table to describe"
#             },
#             "database": {
#                 "type": "string",
#                 "description": "Database name (optional)"
#             }
#         }
#     },
#     {
#         "name": "run_query",
#         "description": "Run a SQL query on ClickHouse",
#         "parameters": {
#             "query": {
#                 "type": "string",
#                 "description": "SQL query to execute"
#             }
#         }
#     }
# ]

# Update DEFAULT_FUNCTION_TOOLS to include ClickHouse tools
DEFAULT_FUNCTION_TOOLS
