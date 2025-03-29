from typing import List, Dict, Any
import pandas as pd
import numpy as np
from agents import Agent, function_tool

from src.utils.agent_hooks import CustomAgentHooks

@function_tool
def find_outliers(data: List[Dict], column_name: str, method: str, threshold: float) -> List[Dict]:
    """
    Finds outliers in the specified column using the chosen method.
    
    Args:
        data: List of dictionaries containing the data
        column_name: The column to check for outliers
        method: The method to use ('z_score' or 'iqr')
        threshold: Threshold for outlier detection (use 2.0 for z-score, 1.5 for IQR)
    
    Returns:
        A list of dictionaries containing the outliers
    """
    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Check if column exists
        if column_name not in df.columns:
            return f"Error: Column '{column_name}' not found in data"
        
        # Extract numeric data
        numeric_data = pd.to_numeric(df[column_name], errors='coerce')
        df[column_name] = numeric_data
        
        # Remove nulls
        df_clean = df.dropna(subset=[column_name])
        
        # Identify outliers
        outliers = None
        
        if method.lower() == "z_score":
            # Z-score method
            z_scores = np.abs((numeric_data - numeric_data.mean()) / numeric_data.std())
            outliers = df[z_scores > threshold]
        elif method.lower() == "iqr":
            # IQR method
            Q1 = numeric_data.quantile(0.25)
            Q3 = numeric_data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(numeric_data < (Q1 - threshold * IQR)) | (numeric_data > (Q3 + threshold * IQR))]
        else:
            return f"Error: Method '{method}' not supported. Use 'z_score' or 'iqr'."
        
        # Return outliers as list of dictionaries
        if outliers is not None and not outliers.empty:
            return outliers.to_dict('records')
        else:
            return []
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool
def find_correlation(data: List[Dict], column1: str, column2: str) -> Dict[str, Any]:
    """
    Calculates the correlation between two columns in the data.
    
    Args:
        data: List of dictionaries containing the data
        column1: First column name
        column2: Second column name
    
    Returns:
        Dictionary with correlation coefficient and interpretation
    """
    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Check if columns exist
        if column1 not in df.columns:
            return f"Error: Column '{column1}' not found in data"
        if column2 not in df.columns:
            return f"Error: Column '{column2}' not found in data"
        
        # Convert to numeric
        df[column1] = pd.to_numeric(df[column1], errors='coerce')
        df[column2] = pd.to_numeric(df[column2], errors='coerce')
        
        # Remove rows with NaN values
        df_clean = df.dropna(subset=[column1, column2])
        
        if df_clean.empty:
            return {"error": "No valid numeric data found in the specified columns"}
        
        # Calculate correlation
        corr = df_clean[column1].corr(df_clean[column2])
        
        # Interpret correlation
        if abs(corr) < 0.3:
            strength = "weak"
        elif abs(corr) < 0.7:
            strength = "moderate"
        else:
            strength = "strong"
            
        direction = "positive" if corr > 0 else "negative"
        
        if abs(corr) < 0.1:
            interpretation = f"There is virtually no correlation between {column1} and {column2}."
        else:
            interpretation = f"There is a {strength} {direction} correlation ({corr:.3f}) between {column1} and {column2}."
        
        return {
            "correlation_coefficient": corr,
            "strength": strength,
            "direction": direction,
            "interpretation": interpretation
        }
    except Exception as e:
        return f"Error: {str(e)}"

def create_analyst_agent():
    """
    Creates and returns the data analyst agent
    """
    analyst_agent = Agent(
        name="Data Analyst Agent",
        instructions="""
        You are a data analysis expert. You can help users analyze data from ClickHouse queries.
        
        You can perform the following types of analysis:
        1. Find outliers in a specific column of the data
        2. Find correlations between two columns in the data
        
        You have the following tools:
        - find_outliers: Find outliers in a column using z-score or IQR methods
          - For method parameter, use 'z_score' or 'iqr'
          - For threshold parameter, use 2.0 for z-score or 1.5 for IQR
        - find_correlation: Calculate correlation between two columns
        
        Always wait for the data first, which should come from the ClickHouse agent.
        When finding outliers, suggest appropriate columns to analyze and explain the results.
        When finding correlations, help users understand the meaning of the correlation values.
        """,
        tools=[find_outliers, find_correlation],
        hooks=CustomAgentHooks(display_name="Data Analyst Agent"),
    )
    
    return analyst_agent 