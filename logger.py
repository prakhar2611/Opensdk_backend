import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent_runs.log")
    ]
)

# Create logger
logger = logging.getLogger("agent_creator")
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture detailed information

# Set debug mode based on environment variable
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Create a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)

# Create a file handler
log_file = "agent_runs.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

def setup_logger():
    """Ensure the logger is set up correctly"""
    logger.debug("Logger initialized with DEBUG level enabled")
    return logger

def debug(message):
    """Log debug message if DEBUG is enabled"""
    if DEBUG:
        logger.debug(message)

def info(message):
    """Log info message"""
    logger.info(message)

def warning(message):
    """Log warning message"""
    logger.warning(message)

def error(message):
    """Log error message"""
    logger.error(message)

def critical(message):
    """Log critical message"""
    logger.critical(message) 