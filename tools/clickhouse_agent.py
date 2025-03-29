from typing import List, Dict, Any
from agents import Agent, function_tool
import logging
import os
from dotenv import load_dotenv
from clickhouse_connect.driver.binding import quote_identifier, format_query_value


from utils.agent_hooks import CustomAgentHooks
from utils.clickhouse_utils import get_clickhouse_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# @function_tool
# def show_databases() -> List[str]:
#     """
#     Show all databases in the ClickHouse server.
#     Returns a list of database names.
#     """
#     logger.info("="*60)
#     logger.info("📋 FUNCTION TOOL: show_databases")
#     logger.info("="*60)
    
#     # Force reload env variables
#     load_dotenv(override=True)
#     logger.info(f"Environment CLICKHOUSE_HOST: {os.environ.get('CLICKHOUSE_HOST', 'NOT SET')}")
#     logger.info(f"Environment CLICKHOUSE_DATABASE: {os.environ.get('CLICKHOUSE_DATABASE', 'NOT SET')}")
    
#     try:
#         logger.info("Creating ClickHouse client...")
#         client = get_clickhouse_client()
        
#         logger.info("Executing SHOW DATABASES query...")
#         result = client.query("SHOW DATABASES")
        
#         databases = [row[0] for row in result.result_rows]
#         logger.info(f"Found {len(databases)} databases: {databases}")
#         return databases
#     except Exception as e:
#         logger.error(f"❌ Error in show_databases: {str(e)}")
#         logger.exception("Detailed error information:")
#         return f"Error: {str(e)}"


# @function_tool
# def show_tables(database: str = None) -> List[str]:
#     """
#     Show all tables in the specified ClickHouse database.
#     If no database is specified, uses the default database from connection.
#     Returns a list of table names.
#     """
#     logger.info("="*60)
#     logger.info("📋 FUNCTION TOOL: show_tables")
#     logger.info(f"Database parameter: {database}")
#     logger.info("="*60)
    
#     # Force reload env variables
#     load_dotenv(override=True)
#     logger.info(f"Environment CLICKHOUSE_HOST: {os.environ.get('CLICKHOUSE_HOST', 'NOT SET')}")
#     logger.info(f"Environment CLICKHOUSE_DATABASE: {os.environ.get('CLICKHOUSE_DATABASE', 'NOT SET')}")
    
#     try:
#         logger.info(f"Creating ClickHouse client with database={database}...")
#         client = get_clickhouse_client(database=database)
        
#         # Log which database we're actually connected to
#         logger.info(f"Client connected to database: {client.database}")
        
#         if database:
#             logger.info(f"Executing SHOW TABLES FROM {database} query...")
#             result = client.query(f"SHOW TABLES FROM {database}")
#         else:
#             logger.info("Executing SHOW TABLES query on default database...")
#             result = client.query("SHOW TABLES")
        
#         tables = [row[0] for row in result.result_rows]
#         logger.info(f"Found {len(tables)} tables: {tables}")
#         return tables
#     except Exception as e:
#         logger.error(f"❌ Error in show_tables: {str(e)}")
#         logger.exception("Detailed error information:")
#         return f"Error: {str(e)}"


# @function_tool
# def describe_table(table: str, database: str = None) -> List[Dict[str, str]]:
#     """
#     Describe the structure of a specified table.
#     If no database is specified, uses the default database from connection.
#     Returns the table structure with column names and types.
#     """
#     logger.info("="*60)
#     logger.info("📋 FUNCTION TOOL: describe_table")
#     logger.info(f"Table parameter: {table}")
#     logger.info(f"Database parameter: {database}")
#     logger.info("="*60)
    
#     # Force reload env variables
#     load_dotenv(override=True)
#     logger.info(f"Environment CLICKHOUSE_HOST: {os.environ.get('CLICKHOUSE_HOST', 'NOT SET')}")
#     logger.info(f"Environment CLICKHOUSE_DATABASE: {os.environ.get('CLICKHOUSE_DATABASE', 'NOT SET')}")
    
#     try:
#         # Make sure database parameter is passed to the client
#         logger.info(f"Creating ClickHouse client with database={database}...")
#         client = get_clickhouse_client(database=database)
        
#         # Log database info from client
#         logger.info(f"Client connected to database: {client.database}")
        
#         # Construct and execute query
#         if database:
#             query = f"DESCRIBE TABLE {database}.{table}"
#         else:
#             query = f"DESCRIBE TABLE {table}"
        
#         logger.info(f"Executing query: {query}")
#         result = client.query(query)
        
#         # Convert to a list of dictionaries for better readability
#         columns = []
#         for row in result.result_rows:
#             columns.append({
#                 "name": row[0],
#                 "type": row[1],
#                 "default_type": row[2],
#                 "default_expression": row[3]
#             })
        
#         logger.info(f"Found {len(columns)} columns in table {table}")
#         for i, col in enumerate(columns):
#             logger.info(f"  Column {i+1}: {col['name']} ({col['type']})")
        
#         return columns
#     except Exception as e:
#         logger.error(f"❌ Error in describe_table: {str(e)}")
#         logger.exception("Detailed error information:")
#         return f"Error: {str(e)}"

# @function_tool
# def run_query(query: str, database: str = None) -> List[Dict]:
#     """
#     Run a custom SQL query on ClickHouse.
#     Returns the query results as a list of dictionaries.
#     Use with caution, as this allows arbitrary SQL execution.
    
#     Args:
#         query (str): The SQL query to execute
#         database (str, optional): The database to run the query against
#     """
#     logger.info("="*60)
#     logger.info("📋 FUNCTION TOOL: run_query")
#     logger.info(f"Query: {query}")
#     logger.info(f"Database parameter: {database}")
#     logger.info("="*60)
    
#     # Force reload env variables
#     load_dotenv(override=True)
#     logger.info(f"Environment CLICKHOUSE_HOST: {os.environ.get('CLICKHOUSE_HOST', 'NOT SET')}")
#     logger.info(f"Environment CLICKHOUSE_DATABASE: {os.environ.get('CLICKHOUSE_DATABASE', 'NOT SET')}")
    
#     try:
#         # Determine if there's an explicit USE database statement
#         detected_db = None
#         if query.lower().startswith("use "):
#             # Extract database name from USE statement
#             db_line = query.split('\n')[0]
#             detected_db = db_line.split(' ')[1].strip(';').strip()
#             logger.info(f"Detected USE database statement: {detected_db}")
            
#             # Remove the USE statement from the query
#             query = '\n'.join(query.split('\n')[1:])
        
#         # Extract database from query if it contains database.table syntax
#         if ' from ' in query.lower():
#             from_part = query.lower().split(' from ')[1].strip()
#             if '.' in from_part.split(' ')[0]:
#                 db_table = from_part.split(' ')[0]
#                 db_name = db_table.split('.')[0]
#                 logger.info(f"Detected database in FROM clause: {db_name}")
#                 detected_db = db_name
        
#         # Use provided database parameter, detected database, or none
#         db_to_use = database or detected_db
#         logger.info(f"Final database selection: {db_to_use if db_to_use else 'default from env'}")
        
#         # Get client with the appropriate database
#         logger.info(f"Creating ClickHouse client with database={db_to_use}...")
#         client = get_clickhouse_client(database=db_to_use)
        
#         # Log database info from client
#         logger.info(f"Client connected to database: {client.database}")
        
#         # Execute the query
#         logger.info(f"Executing query: {query}")
#         result = client.query(query)
        
#         # Get column names
#         column_names = [col[0] for col in result.column_names]
#         logger.info(f"Query returned columns: {column_names}")
        
#         # Convert to list of dictionaries for better readability
#         rows = []
#         for row in result.result_rows:
#             row_dict = {}
#             for i, col_name in enumerate(column_names):
#                 row_dict[col_name] = row[i]
#             rows.append(row_dict)
        
#         logger.info(f"Query returned {len(rows)} rows")
#         if len(rows) > 0:
#             logger.info(f"First row sample: {rows[0]}")
        
#         return rows
#     except Exception as e:
#         logger.error(f"❌ Error in run_query: {str(e)}")
#         logger.exception("Detailed error information:")
#         return f"Error: {str(e)}"

@function_tool
def describe_table(table: str, database: str = None) -> List[Dict]:
    """
    Describe the structure of a specified ClickHouse table.
    If no database is specified, uses the default database from connection.
    Returns a list of dictionaries containing column names and types.
    """
    
    client = get_clickhouse_client(database=database)

    logger.info(f"Getting schema info for table {database}.{table}")
    schema_query = f"DESCRIBE TABLE {quote_identifier(database)}.{quote_identifier(table)}"
    schema_result = client.query(schema_query)

    columns = []
    column_names = schema_result.column_names
    for row in schema_result.result_rows:
        column_dict = {}
        for i, col_name in enumerate(column_names):
            column_dict[col_name] = row[i]
       
        columns.append(column_dict)

    create_table_query = f"SHOW CREATE TABLE {database}.`{table}`"
    create_table_result = client.command(create_table_query)

    return {
        "database": database,
        "name": table,
        "columns": columns,
        "create_table_query": create_table_result,
    }    


@function_tool
def run_query(query: str, database: str = None) -> List[Dict]:
    """
    Run a custom SQL query on ClickHouse.
    Returns the query results as a list of dictionaries.
    Use with caution, as this allows arbitrary SQL execution.
    """
    client = get_clickhouse_client(database=database)
    try:
        res = client.query(query, settings={"readonly": 1})
        column_names = res.column_names
        rows = []
        for row in res.result_rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = row[i]
            rows.append(row_dict)
        logger.info(f"Query returned {len(rows)} rows")
        return rows
    except Exception as err:
        logger.error(f"Error executing query: {err}")
        return f"error running query: {err}"
