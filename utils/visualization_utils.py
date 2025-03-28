import json
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

def is_time_series(data: List[Dict]) -> Tuple[bool, Optional[str]]:
    """
    Determine if the data contains a time series column.
    
    Args:
        data: List of dictionaries containing the data
        
    Returns:
        Tuple[bool, Optional[str]]: (is_time_series, time_column_name)
    """
    if not data:
        return False, None
        
    # Convert to pandas DataFrame for easier analysis
    df = pd.DataFrame(data)
    
    # Check for common time/date column names
    common_time_cols = ['time', 'date', 'datetime', 'timestamp', 'created_at', 'updated_at']
    for col in common_time_cols:
        if col in df.columns:
            return True, col
    
    # Check if any columns can be parsed as datetime
    for col in df.columns:
        # Skip if column is not string-like
        if not pd.api.types.is_string_dtype(df[col].dtype):
            continue
            
        # Try to parse as datetime
        try:
            # Take a sample of non-null values
            sample = df[col].dropna().iloc[:5]
            if len(sample) > 0:
                pd.to_datetime(sample)
                return True, col
        except (ValueError, TypeError):
            pass
    
    return False, None

def is_plottable(data: List[Dict]) -> bool:
    """
    Determine if the data can be plotted.
    
    Args:
        data: List of dictionaries containing the data
        
    Returns:
        bool: True if data can be plotted
    """
    if not data:
        return False
        
    # Convert to pandas DataFrame
    df = pd.DataFrame(data)
    
    # Need at least one numeric column to plot
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    return len(numeric_columns) > 0

def determine_chart_type(data: List[Dict]) -> str:
    """
    Determine the best chart type for the data.
    
    Args:
        data: List of dictionaries containing the data
        
    Returns:
        str: Chart type ('line', 'bar', 'scatter', 'pie')
    """
    if not data:
        return 'line'  # Default
        
    # Convert to pandas DataFrame
    df = pd.DataFrame(data)
    
    # Check if it's time series
    is_ts, _ = is_time_series(data)
    if is_ts:
        return 'line'
        
    # Count number of records
    num_records = len(df)
    
    # Count number of numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    num_numeric = len(numeric_columns)
    
    # Count categorical columns
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    # If few records with one numeric column, pie chart could be good
    if num_records <= 10 and num_numeric == 1 and len(categorical_columns) >= 1:
        return 'pie'
    
    # If few records, bar chart is often better than line
    if num_records <= 20:
        return 'bar'
    
    # If many records, line chart is often better
    if num_records > 100:
        return 'line'
        
    # If multiple numeric columns, scatter can be good
    if num_numeric >= 2:
        return 'scatter'
        
    # Default to bar chart
    return 'bar'

def generate_html_plot(data: List[Dict], title: str = "Data Visualization") -> str:
    """
    Generate HTML with JavaScript for plotting the data using Chart.js.
    
    Args:
        data: List of dictionaries containing the data
        title: Title of the chart
        
    Returns:
        str: HTML string with embedded JavaScript for the chart
    """
    if not data:
        return "<p>No data to visualize</p>"
        
    # Convert to pandas DataFrame
    df = pd.DataFrame(data)
    
    # Check if data is plottable
    if not is_plottable(data):
        return "<p>Data cannot be visualized as a chart</p>"
    
    # Determine chart type
    chart_type = determine_chart_type(data)
    
    # Check for time series data
    is_ts, time_col = is_time_series(data)
    
    # Select columns for visualization
    x_axis_col = time_col if is_ts else df.columns[0]
    
    # Find numeric columns for y-axis
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # If x-axis is numeric and in numeric_columns, remove it for y-axis
    if x_axis_col in numeric_columns:
        numeric_columns.remove(x_axis_col)
    
    # If no numeric columns left, try to use the first column
    if not numeric_columns and len(df.columns) > 1:
        numeric_columns = [df.columns[1]]
    
    # If still no numeric columns, return error
    if not numeric_columns:
        return "<p>No suitable numeric columns found for visualization</p>"
    
    # Prepare data for Chart.js
    x_values = df[x_axis_col].tolist()
    
    # Format dates if time series
    if is_ts:
        try:
            x_values = [pd.to_datetime(x).strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None for x in x_values]
        except Exception:
            # If date formatting fails, use as-is
            pass
    
    # Create datasets for Chart.js
    datasets = []
    for col in numeric_columns[:5]:  # Limit to 5 series for readability
        try:
            # Convert to float and handle NaN
            y_values = [float(y) if pd.notna(y) else None for y in df[col].tolist()]
            
            # Generate a color based on the index
            hue = (numeric_columns.index(col) * 137) % 360
            color = f"hsla({hue}, 70%, 60%, 0.8)"
            
            datasets.append({
                "label": col,
                "data": y_values,
                "backgroundColor": color,
                "borderColor": color.replace("0.8", "1.0"),
                "borderWidth": 2,
                "fill": False
            })
        except (ValueError, TypeError):
            continue
    
    # Generate Chart.js configuration
    chart_config = {
        "type": chart_type,
        "data": {
            "labels": x_values,
            "datasets": datasets
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {
                    "display": True,
                    "text": title
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False
                }
            },
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": x_axis_col
                    }
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": "Value"
                    }
                }
            }
        }
    }
    
    # Special options for time series
    if is_ts:
        chart_config["options"]["scales"]["x"]["type"] = "time"
        chart_config["options"]["scales"]["x"]["time"] = {
            "parser": "yyyy-MM-dd HH:mm:ss",
            "tooltipFormat": "ll HH:mm"
        }
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .chart-container {{
            height: 600px;
            position: relative;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        .data-table {{
            margin-top: 30px;
            width: 100%;
            border-collapse: collapse;
        }}
        .data-table th, .data-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .data-table th {{
            background-color: #f2f2f2;
        }}
        .data-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="chart-container">
            <canvas id="dataChart"></canvas>
        </div>
        
        <h2>Data Table</h2>
        <div style="overflow-x: auto;">
            <table class="data-table">
                <thead>
                    <tr>
                        {"".join([f"<th>{col}</th>" for col in df.columns])}
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr>{''.join([f'<td>{str(row[col]) if pd.notna(row[col]) else ''}</td>' for col in df.columns])}</tr>" for _, row in df.head(50).iterrows()])}
                </tbody>
            </table>
            {"<p><em>Note: Showing first 50 rows</em></p>" if len(df) > 50 else ""}
        </div>
    </div>

    <script>
        const ctx = document.getElementById('dataChart').getContext('2d');
        const chartConfig = {json.dumps(chart_config)};
        new Chart(ctx, chartConfig);
    </script>
</body>
</html>
"""
    
    return html

def save_html_plot(data: List[Dict], filename: str, title: str = "Data Visualization") -> str:
    """
    Save data visualization as an HTML file.
    
    Args:
        data: List of dictionaries containing the data
        filename: File name to save the HTML (without extension)
        title: Title of the chart
        
    Returns:
        str: Path to the saved HTML file
    """
    html_content = generate_html_plot(data, title)
    
    # Ensure the filename has .html extension
    if not filename.endswith('.html'):
        filename += '.html'
    
    # Save the file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return os.path.abspath(filename) 