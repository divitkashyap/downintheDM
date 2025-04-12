from dotenv import load_dotenv
from portia import (default_config, Portia,)
from custom_tool_registry import custom_tool_registry
from custom_config import get_my_config
from portia.open_source_tools.
import os
import asyncio

load_dotenv()

# Initialize Portia with your custom tools
def run_with_portia():
    print("\n🤖 Initializing Portia with Instagram Tools")
    
    # Create Portia configuration
    config = get_my_config()
    
    # Initialize Portia with your tools (passing tool_registry as separate argument)
    portia_instance = Portia(
        config=config,tools=custom_tool_registry, 
    )
    
    # Run a command that will use your Instagram tools
    print("\n📱 Running Instagram task with Portia...")
    response = portia_instance.run(
        "Log into my Instagram account and check my direct messages. Summarize any unread messages."
    )
    
    # Display the AI's response
    print("\n🤖 Portia's Response:")
    print("=" * 60)
    print(response.text)
    print("=" * 60)
    
    # Access tool execution results if needed
    print("\n📊 Tool Execution Results:")
    for result in response.run_history:
        if result.tool_call:
            print(f"Tool: {result.tool_call.name}")
            print(f"Status: {'Success' if result.tool_result else 'Failed'}")
            if result.tool_result:
                print(f"Result: {result.tool_result}")
            print("-" * 40)

if __name__ == "__main__":
    run_with_portia()