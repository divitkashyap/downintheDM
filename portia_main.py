from dotenv import load_dotenv
from portia import Portia, Clarification
from portia import InMemoryToolRegistry
from custom_config import get_my_config
from custom_tool_registry import InstagramAuthenticationTool, InstagramMessagesSummaryTool
import os
import json

load_dotenv()

def run_with_portia():
    print("\n🤖 Initializing Portia with Instagram Tools")
    
    # Get your custom config
    config = get_my_config()
    
    # Create proper tool registry using Portia's InMemoryToolRegistry
    tools_registry = InMemoryToolRegistry.from_local_tools([
        InstagramAuthenticationTool(),
        InstagramMessagesSummaryTool()
    ])
    
    # Initialize Portia with both config and tools
    portia_instance = Portia(
        config=config,
        tools=tools_registry
    )
    
    # Get credentials upfront
    instagram_username = os.environ.get("INSTAGRAM_USERNAME")
    instagram_password = os.environ.get("INSTAGRAM_PASSWORD")
    
    if not instagram_username or not instagram_password:
        print("❌ Instagram credentials not found in environment variables.")
        print("Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file.")
        return
    
    # Add credentials to the initial prompt
    print("\n📱 Running Instagram task with Portia...")
    response = portia_instance.run(
        f"Log into my Instagram account with username '{instagram_username}' and password '{instagram_password}'. Check my direct messages and summarize any unread messages."
    )
    
    # Handle clarifications if needed
    if response.state == "NEED_CLARIFICATION" and response.outputs and response.outputs.clarifications:
        print("\n⚠️ Need to resolve clarifications...")
        
        # Resolve each clarification
        for clarification in response.outputs.clarifications:
            print(f"Resolving: {clarification.user_guidance}")
            
            if "username" in clarification.user_guidance.lower():
                portia_instance.resolve_clarification(
                    clarification=clarification,
                    response=instagram_username
                )
                print(f"✅ Provided username: {instagram_username}")
                
            elif "password" in clarification.user_guidance.lower():
                portia_instance.resolve_clarification(
                    clarification=clarification,
                    response=instagram_password
                )
                print(f"✅ Provided password: {'*' * len(instagram_password)}")
        
        # Resume execution
        print("\n▶️ Resuming execution with provided credentials...")
        response = portia_instance.resume(response)
    
    # Display the AI's response - using the correct attributes
    print("\n🤖 Portia's Response:")
    print("=" * 60)
    
    if hasattr(response, 'outputs') and response.outputs and hasattr(response.outputs, 'final_output'):
        print(response.outputs.final_output.get_value())
    else:
        print("No final output available")
    
    print("=" * 60)
    
    # Print available response attributes for debugging
    print("\n📊 Response Structure:")
    print(f"Response type: {type(response).__name__}")
    print(f"Available attributes: {dir(response)}")
    
    # Try to safely print steps if available
    if hasattr(response, 'steps') and response.steps:
        print("\nSteps:")
        for i, step in enumerate(response.steps):
            print(f"Step {i+1}: {step}")

if __name__ == "__main__":
    run_with_portia()