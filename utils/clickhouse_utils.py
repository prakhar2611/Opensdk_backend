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
    

    # Determine which database to use
    if database:
        db_name = database
    else:
        db_name = os.environ.get("CLICKHOUSE_DATABASE")
        if not db_name:
            logger.warning("CLICKHOUSE_DATABASE not set in .env file. Using default database.")
            db_name = "default"
    
    
    logger.info(f"Database: {db_name}")
    logger.info(f"Username: {username}")
    
    
    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=db_name,
            secure=False,
            verify=False
        )

        return client
        
    except Exception as e:
        logger.error(f"❌ Error connecting to ClickHouse: {str(e)}")
        logger.error(f"Connection parameters: host={host}, port={port}, database={db_name}, username={username}")
        raise
