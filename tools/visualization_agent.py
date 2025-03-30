from typing import List, Dict, Any
from agents import Agent, function_tool
import os
import pandas as pd
import json

from utils.agent_hooks import CustomAgentHooks
from utils.visualization_utils import (
    generate_html_plot, 
    save_html_plot,
    is_time_series,
    is_plottable,
    determine_chart_type
)

@function_tool
def visualize_data(data_input: str) -> str:
    """
    Visualizes the data and returns the HTML content.
    
    Args:
        data_input: JSON string with the following structure:
            {
                "data": List of dictionaries containing the data,
                "title": (Optional) Title of the chart
            }
        
    Returns:
        str: HTML content with the visualization
    """
    # Parse input JSON
    try:
        input_dict = json.loads(data_input)
        data = input_dict.get("data", [])
        title = input_dict.get("title")
    except (json.JSONDecodeError, TypeError):
        return "Invalid input format. Please provide a valid JSON string."
    
    if not data:
        return "No data to visualize"
    
    # Set default title if none provided
    if not title:
        title = "ClickHouse Data Visualization"
    
    # Check if data is plottable
    if not is_plottable(data):
        return "The data cannot be visualized as a chart because it doesn't contain numeric columns"
    
    # Generate the HTML for the plot
    html_content = generate_html_plot(data, title)
    
    return html_content

