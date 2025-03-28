import os
import logging
from dotenv import load_dotenv
import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_clickhouse_client(database=None, tables=None):
    """Get a ClickHouse client using environment variables"""
    # Force reload environment variables to ensure fresh values
    load_dotenv(override=True)
    
    # Get connection details from environment
    host = os.environ.get("CLICKHOUSE_HOST")
    port = os.environ.get("CLICKHOUSE_PORT")
    username = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD", "")
    
    # Validate host and port
    if not host:
        logger.error("CLICKHOUSE_HOST environment variable is not set or empty. Check your .env file.")
        host = "localhost"  # Fallback
        
    if not port:
        logger.error("CLICKHOUSE_PORT environment variable is not set or empty. Check your .env file.")
        port = "8123"  # Fallback
        
    # Convert port to integer
    try:
        port = int(port)
    except ValueError:
        logger.error(f"Invalid CLICKHOUSE_PORT value: {port}. Using default 8123.")
        port = 8123
    
    # Determine which database to use
    if database:
        db_name = database
    else:
        db_name = os.environ.get("CLICKHOUSE_DATABASE")
        if not db_name:
            logger.warning("CLICKHOUSE_DATABASE not set in .env file. Using default database.")
            db_name = "default"
    
    # Log connection details
    logger.info("="*80)
    logger.info("🔌 CLICKHOUSE CONNECTION DETAILS")
    logger.info(f"Environment file (.env) values:")
    logger.info(f"CLICKHOUSE_HOST: {os.environ.get('CLICKHOUSE_HOST', 'NOT SET')}")
    logger.info(f"CLICKHOUSE_PORT: {os.environ.get('CLICKHOUSE_PORT', 'NOT SET')}")
    logger.info(f"CLICKHOUSE_DATABASE: {os.environ.get('CLICKHOUSE_DATABASE', 'NOT SET')}")
    logger.info(f"CLICKHOUSE_USER: {os.environ.get('CLICKHOUSE_USER', 'NOT SET')}")
    logger.info("="*80)
    logger.info(f"Actual connection parameters being used:")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Database: {db_name}")
    logger.info(f"Username: {username}")
    
    if tables:
        if isinstance(tables, str):
            tables_list = [t.strip() for t in tables.split(",")]
            logger.info(f"Tables specified: {tables_list}")
        else:
            logger.info(f"Tables specified: {tables}")
    logger.info("="*80)
    
    try:
        logger.info(f"Attempting connection to {host}:{port} with database '{db_name}'")
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=db_name
        )
        
        # Test connection
        logger.info("Testing connection with SELECT 1 query...")
        result = client.query("SELECT 1")
        if result.result_rows and result.result_rows[0][0] == 1:
            logger.info(f"✅ Successfully connected to ClickHouse database: {db_name}")
            
            # Check tables if specified
            if tables:
                try:
                    if isinstance(tables, str):
                        tables_to_check = [t.strip() for t in tables.split(",")]
                    else:
                        tables_to_check = tables
                        
                    logger.info("Retrieving available tables...")
                    existing_tables = [row[0] for row in client.query("SHOW TABLES").result_rows]
                    logger.info(f"Available tables in {db_name}: {existing_tables}")
                    
                    # Verify each specified table
                    for table in tables_to_check:
                        if isinstance(table, str) and table in existing_tables:
                            logger.info(f"✅ Table verified: {table}")
                        else:
                            logger.warning(f"⚠️ Table not found: {table}")
                except Exception as e:
                    logger.error(f"Error checking tables: {str(e)}")
        
        return client
        
    except Exception as e:
        logger.error(f"❌ Error connecting to ClickHouse: {str(e)}")
        logger.error(f"Connection parameters: host={host}, port={port}, database={db_name}, username={username}")
        raise

def check_db_connectivity():
    """Check if ClickHouse database is reachable and connection settings are correct"""
    try:
        # Force reload environment variables
        load_dotenv(override=True)
        
        # Get connection details for logging
        host = os.environ.get("CLICKHOUSE_HOST", "localhost")
        port = os.environ.get("CLICKHOUSE_PORT", "8123")
        username = os.environ.get("CLICKHOUSE_USER", "default")
        database = os.environ.get("CLICKHOUSE_DATABASE", "default")
        
        logger.info(f"Checking connection to ClickHouse at {host}:{port}...")
        client = get_clickhouse_client()
        
        # Run a simple query to verify connection
        result = client.query("SELECT 1")
        if result.result_rows and result.result_rows[0][0] == 1:
            logger.info(f"✅ Successfully connected to ClickHouse database at {host}:{port}")
            logger.info(f"   Database: {database}")
            logger.info(f"   Username: {username}")
            return True
    except ClickHouseError as e:
        logger.error(f"❌ Failed to connect to ClickHouse: {str(e)}")
        logger.error(f"Connection details:")
        logger.error(f"   Host: {host}")
        logger.error(f"   Port: {port}")
        logger.error(f"   Database: {database}")
        logger.error(f"   Username: {username}")
        logger.error(f"Please check your connection settings in the .env file.")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error when connecting to ClickHouse: {str(e)}")
        return False