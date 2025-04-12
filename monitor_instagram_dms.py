#!/usr/bin/env python3
import os
import time
import json
import subprocess
from datetime import datetime

# File to store previous state
PREVIOUS_STATE_FILE = "previous_instagram_state.json"

def run_instagram_check():
    """Run the Instagram DM checker script"""
    print(f"Running Instagram check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    subprocess.run(["python3", "main.py"])

def load_previous_state():
    """Load previous DM state from file"""
    if os.path.exists(PREVIOUS_STATE_FILE):
        with open(PREVIOUS_STATE_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                return {"unread_count": 0, "last_check": None}
    return {"unread_count": 0, "last_check": None}

def save_current_state():
    """Save current DM state to file"""
    # Read the most recent report
    try:
        with open('instagram_dm_text_report.txt', 'r') as f:
            content = f.read()
            
        # Extract unread count
        unread_match = None
        for line in content.split('\n'):
            if 'Unread Count:' in line:
                try:
                    unread_match = int(line.split(':')[1].strip())
                    break
                except:
                    pass
        
        current_state = {
            "unread_count": unread_match or 0,
            "last_check": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(PREVIOUS_STATE_FILE, 'w') as f:
            json.dump(current_state, f)
            
        return current_state
    except Exception as e:
        print(f"Error saving state: {e}")
        return None

def check_for_new_messages(previous_state, current_state):
    """Compare states and notify if new messages arrived"""
    if previous_state["unread_count"] < current_state["unread_count"]:
        new_messages = current_state["unread_count"] - previous_state["unread_count"]
        print(f"🔔 NEW MESSAGES DETECTED: {new_messages} new unread message(s)!")
        
        # On Mac, show notification
        os.system(f"""
        osascript -e 'display notification "{new_messages} new Instagram message(s)" with title "Instagram DM Alert"'
        """)
    else:
        print("No new messages since last check.")

def main():
    # Load previous state
    previous_state = load_previous_state()
    print(f"Previous state: {previous_state['unread_count']} unread messages")
    
    # Run Instagram check
    run_instagram_check()
    
    # Save new state
    current_state = save_current_state()
    
    if current_state:
        # Check for new messages
        check_for_new_messages(previous_state, current_state)

if __name__ == "__main__":
    main()