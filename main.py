from dotenv import load_dotenv
import asyncio
import os
import time
from playwright.async_api import async_playwright, TimeoutError

load_dotenv()

# Get Instagram credentials from environment variables
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")

print("\n🔒 Starting Instagram DM Summary Tool")

async def run_instagram_workflow():
    """Run the complete Instagram workflow with proper error handling"""
    
    print("Starting browser...")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    
    try:
        # Step 1: Login to Instagram
        print("\n📱 Logging into Instagram...")
        await page.goto("https://www.instagram.com/")
        
        # Handle cookie consent dialog if it appears
        try:
            print("Checking for cookie consent dialog...")
            cookie_selector = 'button:has-text("Decline optional cookies"), button:has-text("Reject"), button:has-text("Decline")'
            cookie_button = await page.wait_for_selector(cookie_selector, timeout=5000)
            if cookie_button:
                await cookie_button.click()
                print("✅ Clicked 'Reject' on cookie dialog")
                await page.wait_for_timeout(1000) # Wait for dialog to close
        except Exception as e:
            print(f"No cookie dialog or couldn't handle it: {e}")
        
        # Wait for and fill login form
        await page.wait_for_selector('input[name="username"]')
        await page.fill('input[name="username"]', INSTAGRAM_USERNAME)
        await page.fill('input[name="password"]', INSTAGRAM_PASSWORD)
        
        # Take screenshot of login page
        await page.screenshot(path="1_login_page.png")
        print("✅ Screenshot saved: 1_login_page.png")
        
        # Click login button
        await page.click('button[type="submit"]')
        print("Clicked login button, waiting for home page...")
        
        # Handle verification if needed
        try:
            verification_selector = 'input[name="verificationCode"], input[placeholder*="code"]'
            verify_element = await page.wait_for_selector(verification_selector, timeout=8000)
            
            if verify_element:
                await page.screenshot(path="2_verification_page.png")
                print("\n⚠️ Verification required!")
                print("✅ Screenshot saved: 2_verification_page.png")
                print("Please check your email for a code, enter it in the browser")
                print("Waiting for you to complete verification (60 seconds)...")
                
                # Wait for user to enter verification code and click continue
                await page.wait_for_selector('svg[aria-label="Home"], a[href="/direct/inbox/"]', timeout=60000)
        except:
            # No verification needed, continue
            print("No verification needed, continuing...")
        
        # Step 2: First navigate to home page (more reliable)
        print("\n🏠 Navigating to Instagram home page...")
        try:
            # Navigate to home page but DON'T wait for networkidle (which often times out)
            await page.goto("https://www.instagram.com/", timeout=15000)
            # Just wait for basic page load 
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            
            print("Basic page loaded, now checking for UI indicators...")
            
            # Wait for home page to load - look for multiple possible indicators
            home_loaded = False
            for selector in ['svg[aria-label="Home"]', 'a[href="/explore/"]', 'svg[aria-label="Search"]', '[aria-label="Search"]', '[aria-label="Home"]']:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    home_loaded = True
                    print(f"✅ Home page loaded, found indicator: {selector}")
                    break
                except Exception as e:
                    print(f"Didn't find selector '{selector}': {e}")
                    continue

            if not home_loaded:
                # Try one more approach - check if we can find feed elements
                feed_content = await page.evaluate('''
                () => {
                    return document.body.innerText.includes("Stories") || 
                           document.body.innerText.includes("Feed") || 
                           document.body.innerText.includes("Suggested");
                }
                ''')
                
                if feed_content:
                    home_loaded = True
                    print("✅ Home page confirmed loaded via text content check")
            
            if not home_loaded:
                raise Exception("Could not confirm successful login to home page - visual indicators missing")
                
            # Take screenshot of home page
            await page.screenshot(path="2_home_page.png")
            print("✅ Screenshot saved: 2_home_page.png")
            
            # Handle any popups that appear right after login
            print("Checking for popups on home page...")
            for popup_attempt in range(2):
                try:
                    popup_selector = 'button:has-text("Not Now"), button:has-text("Skip"), button:has-text("Not now")'
                    popup_button = await page.wait_for_selector(popup_selector, timeout=3000)
                    if popup_button:
                        await popup_button.click()
                        print(f"✅ Dismissed popup on home page (attempt {popup_attempt+1})")
                        await page.wait_for_timeout(1000)
                except Exception as e:
                    print(f"No popup detected or error: {e}")
                    break
            
            # NOW navigate to direct messages
            print("\n📨 Navigating to Instagram DMs...")
            
            dm_clicked = False
            
            # Try multiple DM navigation approaches
            
            # Approach 1: Try clicking on Direct Messages icon (most common)
            dm_selectors = [
                'a[href="/direct/inbox/"]',
                'svg[aria-label="Direct"]', 
                'svg[aria-label="Messenger"]',
                'svg[aria-label="Messages"]'
            ]
            
            for dm_selector in dm_selectors:
                try:
                    print(f"Looking for DM icon with selector: {dm_selector}")
                    dm_button = await page.wait_for_selector(dm_selector, timeout=2000)
                    if dm_button:
                        await dm_button.click()
                        print(f"✅ Clicked on DM icon using selector: {dm_selector}")
                        dm_clicked = True
                        await page.wait_for_timeout(3000)  # Wait for navigation
                        break
                except Exception as e:
                    print(f"Couldn't click DM with selector {dm_selector}: {e}")
                    continue
            
            # Approach 2: Try clicking on the paper airplane icon
            if not dm_clicked:
                try:
                    print("Looking for paper airplane icon...")
                    await page.evaluate('''
                    () => {
                        // Find and click on paper airplane icon (common for Messages)
                        const svgs = Array.from(document.querySelectorAll('svg'));
                        for (const svg of svgs) {
                            // Look for paper airplane shape in SVG path
                            if (svg.innerHTML.includes('M22') && svg.innerHTML.includes('polygon') && 
                                (svg.parentElement.getAttribute('aria-label') || "").includes("essage")) {
                                svg.parentElement.click();
                                return true;
                            }
                        }
                        return false;
                    }
                    ''')
                    dm_clicked = True
                    await page.wait_for_timeout(3000)  # Wait for navigation
                    print("✅ Clicked on paper airplane icon")
                except Exception as e:
                    print(f"Could not find paper airplane icon: {e}")
            
            # Approach 3: Try direct URL navigation as last resort
            if not dm_clicked:
                print("Could not find DM icon, trying direct navigation...")
                await page.goto("https://www.instagram.com/direct/inbox/", timeout=15000)
                await page.wait_for_load_state("domcontentloaded", timeout=10000)  # Just wait for DOM, not networkidle
                print("✅ Navigated directly to inbox URL")
            
            # Verify we're on the DMs page
            dm_page_loaded = False
            
            # Check URL first (most reliable)
            if "/direct/" in page.url or "/inbox/" in page.url:
                dm_page_loaded = True
                print("✅ DM page confirmed via URL check")
            else:
                # Try visual indicators
                for indicator in ['[aria-label="Chats"]', 'div[role="listbox"]', 'div[aria-label="Messages"]']:
                    try:
                        await page.wait_for_selector(indicator, timeout=3000)
                        dm_page_loaded = True
                        print(f"✅ DM page loaded, found indicator: {indicator}")
                        break
                    except:
                        continue
            
            # Handle any notification popups immediately
            await page.wait_for_timeout(2000)  # Brief pause to allow popups to appear
            
            print("Checking for notification popups after DM navigation...")
            notification_selectors = [
                'button:has-text("Not Now")', 
                'button:has-text("Not now")',
                'button:has-text("Skip")',
                'button:has-text("Cancel")'
            ]
            
            for selector in notification_selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=2000)
                    if button:
                        await button.click()
                        print(f"✅ Dismissed popup with text: {selector}")
                        await page.wait_for_timeout(1000)
                        break
                except:
                    continue
            
            # Take screenshot of DM page after popup handling
            await page.screenshot(path="3_dm_page.png")
            print("✅ Screenshot saved: 3_dm_page.png")
            
        except Exception as e:
            print(f"Error navigating to DMs: {e}")
            raise Exception("Navigation to Instagram DMs failed")
        
        print("\n🛡️ Running comprehensive popup check after navigation...")

        # Multiple popup handling attempts with different methods
        for attempt in range(3):  # Try up to 3 times to catch any popups
            try:
                # Check for "Save Login Info" dialog - FIXED without timeout parameter
                save_info_button = await page.query_selector('button:has-text("Not Now"), button:has-text("Skip"), button:has-text("Not now")')
                if save_info_button:
                    await save_info_button.click()
                    print(f"✅ Dismissed 'Save Login Info' popup (attempt {attempt+1})")
                    await page.wait_for_timeout(1000)
                    continue  # Check for more popups
                    
                # Check for notification permission dialog
                notif_button = await page.query_selector('button:has-text("Not Now"), button:has-text("Cancel"), div[role="dialog"] button:first-of-type')
                if notif_button:
                    await notif_button.click()
                    print(f"✅ Dismissed notification dialog (attempt {attempt+1})")
                    await page.wait_for_timeout(1000)
                    continue  # Check for more popups
                    
                # Check for the annoying "Switch to Professional Account" popup
                pro_button = await page.query_selector('button:has-text("Not Now"), [aria-label="Close"]')
                if pro_button:
                    await pro_button.click()
                    print(f"✅ Dismissed 'Switch to Professional Account' popup (attempt {attempt+1})")
                    await page.wait_for_timeout(1000)
                    continue  # Check for more popups
                    
                # Check for login popup (which can appear randomly)
                login_popup = await page.query_selector('div[role="dialog"] img[alt="Instagram"]')
                if (login_popup):
                    print(f"⚠️ Login popup detected (attempt {attempt+1})")
                    
                    # Try clicking outside the dialog
                    await page.mouse.click(50, 50)  # Click in top left corner outside dialog
                    print("✅ Clicked outside login dialog")
                    await page.wait_for_timeout(1000)
                    continue  # Check if popup was dismissed
                    
                # No popups found on this attempt
                print(f"✓ No popups detected on attempt {attempt+1}")
                
                # If this is not the first attempt and we didn't find popups, we can stop checking
                if attempt > 0:
                    break
                    
            except Exception as e:
                print(f"Error during popup check {attempt+1}: {e}")
                # Continue to next attempt
                
        print("✅ Popup check complete, continuing with DM interaction...")

        # Replace your single-conversation username code with this multi-conversation loop:

        print("\n👤 Starting multi-conversation data collection...")

        # Define our target usernames - adjust as needed
        target_usernames = ["divit", "cheesepizzalover911", "rosescanbebluetoo", "S.A.M"]
        all_conversation_data = []  # To store data from each conversation

        # Create the report file
        import time
        multi_report_filename = "instagram_dm_multi_report.txt"

        with open(multi_report_filename, "w", encoding="utf-8") as report:
            report.write("INSTAGRAM DM MULTI-CONVERSATION REPORT\n")
            report.write("====================================\n\n")
            report.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            report.write(f"Account: {INSTAGRAM_USERNAME}\n\n")
            
            # Try each username in sequence, collecting data from all
            for i, username in enumerate(target_usernames):
                report.write(f"\n{'='*50}\n")
                report.write(f"CONVERSATION #{i+1}: {username}\n")
                report.write(f"{'='*50}\n\n")
                
                print(f"\n[{i+1}/{len(target_usernames)}] 🔍 Searching for conversation with '{username}'...")
                conversation_found = False
                
                try:
                    # First make sure we're at the inbox page
                    if not "/direct/inbox/" in page.url:
                        print("Navigating back to inbox...")
                        await page.goto("https://www.instagram.com/direct/inbox/", timeout=15000)
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                        
                        # Handle any popups that might appear
                        try:
                            popup_button = await page.wait_for_selector('button:has-text("Not Now"), button:has-text("Skip")', timeout=2000)
                            if popup_button:
                                await popup_button.click()
                                print("✅ Dismissed popup after navigation")
                                await page.wait_for_timeout(1000)
                        except:
                            pass
                    
                    # Use the selector that worked for "divit" for each username
                    username_selector = f'span:has-text("{username}")'
                    
                    # Try to find the conversation with longer timeout
                    try:
                        conversation = await page.wait_for_selector(username_selector, timeout=8000)
                        if conversation:
                            print(f"✅ Found '{username}' conversation!")
                            
                            # Take screenshot showing what we found
                            await page.screenshot(path=f"found_{username}.png")
                            
                            # Try direct click first
                            try:
                                await conversation.click()
                                print(f"✅ Direct click on {username} conversation")
                                await page.wait_for_timeout(3000)
                            except Exception as e:
                                print(f"Direct click failed: {e}")
                                
                                # If direct click fails, try parent element click with JavaScript
                                print("Trying parent element click...")
                                await page.evaluate(f'''
                                () => {{
                                    const element = document.querySelector('span:has-text("{username}")');
                                    if (element) {{
                                        // Navigate up to find clickable container
                                        let parent = element.parentElement;
                                        for (let i = 0; i < 5 && parent; i++) {{
                                            try {{
                                                parent.click();  // Try clicking each parent
                                                return true;
                                            }} catch (e) {{
                                                parent = parent.parentElement;
                                            }}
                                        }}
                                    }}
                                    return false;
                                }}
                                ''')
                                print(f"✅ Attempted parent clicks for {username}")
                                await page.wait_for_timeout(3000)
                            
                            # Check if navigation occurred
                            if '/direct/t/' in page.url:
                                print(f"✅ Successfully opened conversation with {username}: {page.url}")
                                conversation_found = True
                                
                                # Take screenshot of the conversation
                                screenshot_path = f"conversation_{username}.png"
                                await page.screenshot(path=screenshot_path)
                                print(f"✅ Saved conversation screenshot: {screenshot_path}")
                                
                                # Extract message data
                                print(f"📝 Extracting messages from conversation with {username}...")
                                message_data = await page.evaluate('''
                                () => {
                                    // Try to find message elements
                                    const messages = [];
                                    
                                    // Method 1: Standard message containers
                                    document.querySelectorAll('div[role="row"]').forEach(row => {
                                        if (row.innerText && row.innerText.length > 0) {
                                            messages.push({
                                                text: row.innerText,
                                                is_mine: row.classList.contains('xdl72j9') || 
                                                       row.querySelector('[style*="margin-left: auto"]') !== null,
                                                timestamp: null
                                            });
                                        }
                                    });
                                    
                                    // Method 2: Elements with message-like styling
                                    document.querySelectorAll('div').forEach(div => {
                                        if (div.clientHeight > 20 && div.clientHeight < 300 &&
                                            div.clientWidth > 50 && div.clientWidth < 500 &&
                                            div.innerText && div.innerText.length > 0) {
                                            
                                            const style = window.getComputedStyle(div);
                                            const hasStyle = style.padding !== '0px' || 
                                                            style.borderRadius !== '0px' ||
                                                            style.background !== 'none';
                                            
                                            if (hasStyle) {
                                                const isOutgoing = style.alignSelf === 'flex-end' || 
                                                                 div.getAttribute('style')?.includes('margin-left: auto');
                                                
                                                messages.push({
                                                    text: div.innerText.trim(),
                                                    is_mine: isOutgoing,
                                                    timestamp: null
                                                });
                                            }
                                        }
                                    });
                                    
                                    // Remove duplicates
                                    const unique = [];
                                    const seen = new Set();
                                    messages.forEach(msg => {
                                        if (!seen.has(msg.text)) {
                                            seen.add(msg.text);
                                            unique.push(msg);
                                        }
                                    });
                                    
                                    return {
                                        url: window.location.href,
                                        conversation_id: window.location.href.match(/\\/t\\/(.*?)(\\/|$)/)?.[1] || '',
                                        message_count: unique.length,
                                        messages: unique.slice(0, 10) // Get most recent messages
                                    };
                                }
                                ''')
                                
                                # Store important data from this conversation
                                conversation_data = {
                                    'username': username,
                                    'url': message_data.get('url', ''),
                                    'conversation_id': message_data.get('conversation_id', 'unknown'),
                                    'message_count': message_data.get('message_count', 0),
                                    'messages': message_data.get('messages', []),
                                    'screenshot': screenshot_path
                                }
                                
                                all_conversation_data.append(conversation_data)
                                
                                # Write this conversation's data to the report
                                report.write(f"Username: {username}\n")
                                report.write(f"URL: {conversation_data['url']}\n")
                                report.write(f"Messages Found: {conversation_data['message_count']}\n")
                                report.write(f"Screenshot: {screenshot_path}\n\n")
                                
                                # Add message content
                                messages = conversation_data['messages']
                                if messages:
                                    report.write("MOST RECENT MESSAGES:\n")
                                    report.write("-------------------\n\n")
                                    
                                    for idx, msg in enumerate(messages):
                                        sender = "You" if msg.get('is_mine') else username
                                        timestamp = f" ({msg.get('timestamp')})" if msg.get('timestamp') else ""
                                        report.write(f"[{idx+1}] {sender}{timestamp}: {msg.get('text')}\n\n")
                                else:
                                    report.write("No messages could be extracted.\n")
                                    report.write(f"Please check screenshot: {screenshot_path}\n\n")
                            else:
                                print(f"⚠️ Clicked on {username} but didn't navigate to conversation")
                                report.write(f"⚠️ ERROR: Could click on '{username}' but didn't open conversation\n\n")
                    except Exception as find_error:
                        print(f"Could not find conversation with '{username}': {find_error}")
                        report.write(f"⚠️ ERROR: Could not find conversation with '{username}'\n")
                        report.write(f"Error details: {find_error}\n\n")
                
                except Exception as e:
                    print(f"Error processing conversation with '{username}': {e}")
                    report.write(f"⚠️ ERROR: Failed to process conversation with '{username}'\n")
                    report.write(f"Error details: {e}\n\n")
                
                finally:
                    # Always try to return to inbox for next iteration
                    if conversation_found:
                        print(f"Returning to inbox for next conversation...")
                        try:
                            # This is more reliable than using browser history
                            await page.goto("https://www.instagram.com/direct/inbox/", timeout=15000)
                            await page.wait_for_load_state("domcontentloaded", timeout=10000)
                            await page.wait_for_timeout(2000)  # Additional wait for UI to stabilize
                        except Exception as nav_error:
                            print(f"Error returning to inbox: {nav_error}")
            
            # Add summary at the end
            report.write("\n\nSUMMARY\n")
            report.write("=======\n\n")
            report.write(f"Total conversations checked: {len(target_usernames)}\n")
            report.write(f"Conversations found: {len(all_conversation_data)}\n")
            
            for convo in all_conversation_data:
                report.write(f"- {convo['username']}: {convo['message_count']} messages\n")

        print(f"\n✅ Multi-conversation report saved to {multi_report_filename}")
        print(f"Successfully processed {len(all_conversation_data)} out of {len(target_usernames)} conversations")

    except Exception as e:
        # Handle errors and take error screenshot
        print(f"\n❌ Error: {e}")
        try:
            await page.screenshot(path="error_state.png")
            print("Error screenshot saved to error_state.png")
        except:
            print("Could not save error screenshot")
    
    finally:
    # Keep browser open for inspection
        print("\nPress Enter to close the browser and exit...")
    try:
        input()  # Wait for user input
        print("Closing browser...")
        
        # Close browser resources first
        await context.close()
        await browser.close()
        await playwright.stop()
        
        # Force immediate program termination
        import sys
        sys.exit(0)  # This ensures the program completely exits
        
    except KeyboardInterrupt:
        print("\nExiting due to keyboard interrupt")
        import sys
        sys.exit(1)
    except Exception as close_error:
        print(f"Error during browser cleanup: {close_error}")
        import sys
        sys.exit(1)

# Run the main function only when directly executed
if __name__ == "__main__":
    try:
        asyncio.run(run_instagram_workflow())
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import sys
        sys.exit(1)
