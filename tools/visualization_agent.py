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


    """
    Creates and returns the visualization agent
    """
    visualization_agent = Agent(
        name="Visualization Agent",
        instructions="""
        You are a data visualization expert. You help users create visual representations of their ClickHouse data.
        
        You can:
        1. Analyze data to determine the best visualization approach
        2. Generate HTML visualizations for data
        3. Save visualizations to HTML files
        
        IMPORTANT: All function tools expect a JSON string as input:
        - analyze_data_for_visualization: Expects JSON with "data" key containing an array of data objects
        - visualize_data: Expects JSON with "data" key (required) and optional "title" key
        - save_visualization: Expects JSON with "data" key (required), optional "filename" and "title" keys
        
        Example usage:
        analyze_data_for_visualization('{"data": [{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}]}')
        visualize_data('{"data": [{"col1": 1, "col2": "a"}], "title": "My Chart"}')
        save_visualization('{"data": [...], "filename": "my_chart", "title": "My Chart"}')
        
        If the data is time series (has a date/time column), you'll automatically use a line chart.
        For other data types, you'll intelligently select the best chart type based on the data structure.
        
        Always ensure the data is plottable (has numeric columns) before attempting visualization.
        """,
        tools=[analyze_data_for_visualization, visualize_data, save_visualization],
        hooks=CustomAgentHooks(display_name="Visualization Agent"),
    )
    
    return visualization_agent 