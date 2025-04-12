from dotenv import load_dotenv
from portia import Portia, Clarification
from portia import InMemoryToolRegistry
from custom_config import get_my_config
from custom_tool_registry import InstagramAuthenticationTool, InstagramMessagesSummaryTool
import os
import json
import asyncio
from main import run_instagram_workflow

load_dotenv()

def run_with_portia(username=None, password=None):
    """Run the Instagram workflow with credentials from either arguments or .env file"""
    
    # Set environment variables if credentials are provided
    if username:
        os.environ["INSTAGRAM_USERNAME"] = username
    if password:
        os.environ["INSTAGRAM_PASSWORD"] = password
        
    # Check if credentials are available
    if not os.environ.get("INSTAGRAM_USERNAME") or not os.environ.get("INSTAGRAM_PASSWORD"):
        raise ValueError("Missing credentials: Please provide Instagram username and password")
        
    # Run the workflow
    asyncio.run(run_instagram_workflow())
    
    # Return a simple success message
    return {"status": "completed", "message": "Instagram workflow completed successfully"}

# When run directly (for testing)
if __name__ == "__main__":
    # For manual testing, you can provide credentials here
    # run_with_portia("your_username", "your_password")
    
    # Or rely on .env file
    run_with_portia()