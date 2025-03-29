from typing import List, Dict, Any
from agents import Agent, function_tool
import os
import pandas as pd
import json

from src.utils.agent_hooks import CustomAgentHooks
from src.utils.visualization_utils import (
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

@function_tool
def save_visualization(data_input: str) -> str:
    """
    Saves data visualization to an HTML file.
    
    Args:
        data_input: JSON string with the following structure:
            {
                "data": List of dictionaries containing the data,
                "filename": (Optional) Name of the file to save (without extension),
                "title": (Optional) Title of the chart
            }
        
    Returns:
        str: Path to the saved HTML file
    """
    # Parse input JSON
    try:
        input_dict = json.loads(data_input)
        data = input_dict.get("data", [])
        filename = input_dict.get("filename", "clickhouse_visualization")
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
    
    # Save the visualization to an HTML file
    file_path = save_html_plot(data, filename, title)
    
    return f"Visualization saved to: {file_path}"

@function_tool
def analyze_data_for_visualization(data_input: str) -> Dict[str, Any]:
    """
    Analyzes the data to determine the best visualization approach.
    
    Args:
        data_input: JSON string with the following structure:
            {
                "data": List of dictionaries containing the data
            }
        
    Returns:
        Dict: Analysis of the data for visualization purposes
    """
    # Parse input JSON
    try:
        input_dict = json.loads(data_input)
        data = input_dict.get("data", [])
    except (json.JSONDecodeError, TypeError):
        return {"plottable": False, "reason": "Invalid input format. Please provide a valid JSON string."}
    
    if not data:
        return {"plottable": False, "reason": "No data provided"}
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(data)
    
    # Check if data is plottable
    plottable = is_plottable(data)
    
    # Check if it's time series
    is_ts, time_col = is_time_series(data)
    
    # Get best chart type
    chart_type = determine_chart_type(data)
    
    # Get numeric columns
    numeric_columns = df.select_dtypes(include=['number', 'float', 'int']).columns.tolist()
    
    # Get categorical columns
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    # Get dataset size
    row_count = len(df)
    column_count = len(df.columns)
    
    # Provide recommendations
    recommendations = []
    
    if is_ts:
        recommendations.append(f"This appears to be time series data with time column '{time_col}'. A line chart is recommended.")
    
    if len(numeric_columns) > 1:
        recommendations.append(f"Multiple numeric columns found ({', '.join(numeric_columns[:3])}...). You can plot these for comparison.")
    
    if chart_type == 'pie' and len(categorical_columns) > 0:
        recommendations.append(f"Small dataset with categorical data. A pie chart with '{categorical_columns[0]}' as labels would work well.")
    
    return {
        "plottable": plottable,
        "is_time_series": is_ts,
        "time_column": time_col if is_ts else None,
        "recommended_chart_type": chart_type,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "row_count": row_count,
        "column_count": column_count,
        "recommendations": recommendations
    }

def create_visualization_agent():
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