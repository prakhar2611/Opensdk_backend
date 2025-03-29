import asyncio
import os
import json
from dotenv import load_dotenv

from agents import Runner, RunConfig
from src.utils.clickhouse_utils import check_db_connectivity
from experiments.agents import create_clickhouse_agent, create_visualization_agent

# Load environment variables from .env file
load_dotenv()

async def run_visualization_demo():
    """
    Demonstrates the visualization capabilities for ClickHouse data
    """
    try:
        print("🔍 ClickHouse Data Visualization Demo 🔍")
        print("=" * 40)
        
        # Check database connectivity before proceeding
        if not check_db_connectivity():
            print("❌ Cannot connect to ClickHouse database. Please check your connection settings.")
            return
        
        # Get user query for data retrieval
        print("\n📊 This demo will help you visualize data from ClickHouse")
        user_query = input("\n🤔 Enter an SQL query to retrieve data from ClickHouse that you'd like to visualize: ")
        
        # Create agents
        clickhouse_agent = create_clickhouse_agent(database="user_cohort_v2", tables=["monthly_seller_atg_brand"])
        visualization_agent = create_visualization_agent()
        
        # Step 1: Get data from ClickHouse
        print("\n🔄 Retrieving data from ClickHouse...\n")
        clickhouse_result = await Runner.run(
            clickhouse_agent,
            f"run_query({user_query})",
            run_config=RunConfig(
                tracing_disabled=False
            )
        )
        
        data = clickhouse_result.final_output
        
        # Check if we got any data
        if not data or isinstance(data, str) or len(data) == 0:
            print(f"\n❌ Error retrieving data: {data if isinstance(data, str) else 'No data returned'}")
            return
        
        print(f"\n✅ Successfully retrieved {len(data)} rows of data")
        
        # Step 2: Analyze data for visualization
        print("\n🔍 Analyzing data for visualization possibilities...\n")
        
        # Properly format the analyze call to use a properly formatted JSON object
        analysis_input = json.dumps({"data": data})
        analysis_result = await Runner.run(
            visualization_agent,
            f"analyze_data_for_visualization({analysis_input})",
            run_config=RunConfig(
                tracing_disabled=False
            )
        )
        
        analysis = analysis_result.final_output
        
        # Check if data is plottable
        if not analysis.get("plottable", False):
            print(f"\n❌ This data cannot be plotted: {analysis.get('reason', 'No numeric columns')}")
            return
        
        # Print analysis
        print("\n📊 Data Analysis for Visualization:")
        print(f"  - Is time series: {analysis.get('is_time_series', False)}")
        if analysis.get('is_time_series', False):
            print(f"  - Time column: {analysis.get('time_column', '')}")
        print(f"  - Recommended chart type: {analysis.get('recommended_chart_type', '')}")
        print(f"  - Number of rows: {analysis.get('row_count', 0)}")
        print(f"  - Number of columns: {analysis.get('column_count', 0)}")
        print(f"  - Numeric columns: {', '.join(analysis.get('numeric_columns', []))}")
        print(f"  - Categorical columns: {', '.join(analysis.get('categorical_columns', []))}")
        
        if analysis.get('recommendations', []):
            print("\n💡 Recommendations:")
            for rec in analysis.get('recommendations', []):
                print(f"  - {rec}")
        
        # Step 3: Generate visualization filename
        default_filename = "clickhouse_visualization"
        chart_type = analysis.get('recommended_chart_type', 'chart')
        
        # Create a more descriptive filename
        if analysis.get('is_time_series', False):
            time_col = analysis.get('time_column', '')
            numeric_cols = analysis.get('numeric_columns', [])
            if numeric_cols and time_col:
                default_filename = f"{time_col}_vs_{numeric_cols[0]}"
        
        # Ask for filename
        filename = input(f"\n📁 Enter filename for the visualization (default: {default_filename}): ")
        if not filename:
            filename = default_filename
        
        # Ask for title
        default_title = f"ClickHouse Data Visualization - {chart_type.capitalize()} Chart"
        title = input(f"\n📝 Enter title for the visualization (default: {default_title}): ")
        if not title:
            title = default_title
        
        # Step 4: Save visualization
        print("\n💾 Saving visualization...\n")
        
        # Format the save call with proper JSON
        save_input = json.dumps({
            "data": data,
            "filename": filename,
            "title": title
        })
        
        save_result = await Runner.run(
            visualization_agent,
            f"save_visualization({save_input})",
            run_config=RunConfig(
                tracing_disabled=False
            )
        )
        
        # Print result
        print(f"\n🎉 {save_result.final_output}")
        
        # Ask if user wants to view the visualization
        view_response = input("\n👁️ Do you want to open the visualization in a browser? (y/n): ")
        if view_response.lower() in ['y', 'yes']:
            # Get the file path from the result
            file_path = save_result.final_output.split(": ")[-1]
            
            # Open the file in the browser
            import webbrowser
            webbrowser.open(f"file://{file_path}")
            print("\n🌐 Opening visualization in browser...")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        print("\n👋 Thank you for using ClickHouse Data Visualization Demo!")

if __name__ == "__main__":
    asyncio.run(run_visualization_demo()) 