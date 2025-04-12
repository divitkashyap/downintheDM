import logging
from abc import ABC, abstractmethod
import asyncio
from playwright.async_api import async_playwright
import os
from pydantic import BaseModel, Field
from portia import Tool, InMemoryToolRegistry
from typing import Dict, Any, Optional, Type, Tuple, Literal

logger = logging.getLogger(__name__)

# Global variables to maintain state
browser_instance = None
page_instance = None
playwright_instance = None

class BaseTool(ABC):
    """Base class for implementing custom tools"""
    id = None
    description = None
    
    @abstractmethod
    def run(self, params: dict) -> dict:
        pass

class InMemoryToolRegistry:
    def __init__(self, tools=None):
        self.tools = tools or []
        
    @classmethod
    def from_local_tools(cls, tools):
        return cls(tools)

# Define schemas for tool arguments and outputs
class InstagramAuthSchema(BaseModel):
    """Schema for Instagram authentication inputs"""
    username: str = Field(..., description="Instagram username")
    password: str = Field(..., description="Instagram password")

class InstagramAuthOutputSchema(BaseModel):
    """Schema for Instagram authentication outputs"""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Status message")
    screenshot: Optional[str] = Field(None, description="Path to screenshot if available")

class InstagramMessagesSchema(BaseModel):
    """Schema for Instagram Messages inputs (no parameters needed)"""
    pass

class InstagramMessagesOutputSchema(BaseModel):
    """Schema for Instagram Messages outputs"""
    unread_count: int = Field(..., description="Number of unread messages")
    message_previews: list = Field(default_factory=list, description="Preview of messages")
    is_dm_page: bool = Field(..., description="Whether navigation to DMs was successful")

class InstagramAuthenticationTool(Tool):
    # Add type annotations to all fields
    id: str = "instagram_login"
    name: str = "Instagram Login Tool"
    description: str = "Logs into Instagram with username and password using browser automation."
    args_schema: Type[BaseModel] = InstagramAuthSchema
    output_schema: Tuple[str, str] = ("object", "Authentication result with success status")
    should_summarize: bool = True
    
    def run(self, ctx, username: str, password: str) -> Dict[str, Any]:
        """Run the Instagram authentication process"""
        # Your implementation here
        # For example:
        import asyncio
        from main import run_instagram_workflow
        
        # Call your existing Instagram login function
        result = asyncio.run(run_instagram_workflow())
        
        return {
            "success": True,
            "message": "Successfully logged into Instagram",
            "screenshot": "3_home_page.png"
        }

class InstagramMessagesSummaryTool(Tool):
    id: str = "instagram_messages" 
    name: str = "Instagram Messages Summary Tool"
    description: str = "Gets and summarizes Instagram direct messages."
    args_schema: Type[BaseModel] = InstagramMessagesSchema
    output_schema: Tuple[str, str] = ("object", "Message summary with unread count and previews")
    should_summarize: bool = True
    
    def run(self, ctx) -> Dict[str, Any]:
        """Retrieve and summarize Instagram direct messages"""
        # Your implementation here
        # For now, return a placeholder response
        return {
            "unread_count": 2,
            "message_previews": [
                {"sender": "user1", "preview": "Hey there!", "unread": True},
                {"sender": "user2", "preview": "Check this out", "unread": True}
            ],
            "is_dm_page": True
        }

# Create the registry
custom_tool_registry = InMemoryToolRegistry.from_local_tools(
    [
        InstagramAuthenticationTool(),
        InstagramMessagesSummaryTool()
    ]
)
