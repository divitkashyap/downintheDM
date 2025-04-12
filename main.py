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
        
        # Better handling for "Save login info" element
        # print("Checking for 'Save login info' element...")
        # try:
        #     # First try: Look for text content that indicates the save login info screen
        #     login_info_text = await page.evaluate('''
        #     () => {
        #         const bodyText = document.body.innerText;
        #         return bodyText.includes('Save login info') || 
        #                bodyText.includes('Save Login Info') || 
        #                bodyText.includes('Remember login details');
        #     }
        #     ''')
            
        #     if login_info_text:
        #         print("✅ Detected 'Save login info' screen by text content")
                
        #         # Try multiple approaches to find and click the "Not Now" button
        #         button_clicked = False
                
        #         # Approach 1: Direct button selectors
        #         save_info_buttons = [
        #             'button:has-text("Not Now")', 
        #             'button:has-text("Not now")',
        #             'button:has-text("Skip")',
        #             'button[tabindex="0"]:has-text("Not")'
        #         ]
                
        #         for button_selector in save_info_buttons:
        #             try:
        #                 save_button = await page.wait_for_selector(button_selector, timeout=3000)
        #                 if save_button:
        #                     await save_button.click()
        #                     print(f"✅ Clicked '{button_selector}' button")
        #                     button_clicked = True
        #                     await page.wait_for_timeout(2000)  # Longer wait time
        #                     break
        #             except:
        #                 continue
                
        #         # Approach 2: If direct selectors failed, try more aggressive approach
        #         if not button_clicked:
        #             print("Trying alternative approach to find 'Not Now' button...")
        #             clicked = await page.evaluate('''
        #             () => {
        #                 // Find all buttons
        #                 const buttons = Array.from(document.querySelectorAll('button'));
                        
        #                 // Look for buttons containing "Not Now" or "Skip" text
        #                 for (const button of buttons) {
        #                     if (button.innerText.includes('Not Now') || 
        #                         button.innerText.includes('Not now') || 
        #                         button.innerText.includes('Skip')) {
        #                             button.click();
        #                             return true;
        #                     }
        #                 }
                        
        #                 // If no specific button, try any bottom button
        #                 const allButtons = Array.from(document.querySelectorAll('button'));
        #                 if (allButtons.length >= 2) {
        #                     // Often the "Not Now" is the second button
        #                     allButtons[1].click();
        #                     return true;
        #                 }
                        
        #                 return false;
        #             }
        #             ''')
                    
        #             if clicked:
        #                 print("✅ Clicked 'Not Now' button via JavaScript")
        #                 await page.wait_for_timeout(2000)
        #     else:
        #         print("No 'Save login info' screen detected by text content")
        
        # except Exception as e:
        #     print(f"Error handling 'Save login info': {e}")
        #bingo

        # # Handle "Turn on notifications" popup
        # try:
        #     print("Checking for 'Turn on notifications' popup...")
        #     notification_selectors = [
        #         'button:has-text("Not Now")', 
        #         'button:has-text("Skip")',
        #         'button:has-text("Not now")',
        #         'button[tabindex="0"]:has-text("Not")',
        #         # Specific selector for this notification dialog
        #         'h2:has-text("Turn on notifications") ~ div button:last-child'
        #     ]
            
        #     for button_selector in notification_selectors:
        #         try:
        #             notification_button = await page.wait_for_selector(button_selector, timeout=3000)
        #             if notification_button:
        #                 await notification_button.click()
        #                 print(f"✅ Clicked '{button_selector}' on Turn on notifications popup")
        #                 await page.wait_for_timeout(1500) # Wait for dialog to close
        #                 break
        #         except:
        #             continue
        # except Exception as e:
        #     print(f"No notifications popup or couldn't handle it: {e}")

        # # Handle notifications dialog
        # try:
        #     print("Checking for notifications dialog...")
        #     notif_buttons = [
        #         'button:has-text("Not Now")', 
        #         'button:has-text("Skip")',
        #         'button:has-text("Not now")',
        #         'button[tabindex="0"]:has-text("Not")'
        #     ]
            
        #     for button_selector in notif_buttons:
        #         try:
        #             notif_button = await page.wait_for_selector(button_selector, timeout=3000)
        #             if notif_button:
        #                 await notif_button.click()
        #                 print(f"✅ Clicked '{button_selector}' on notifications dialog")
        #                 await page.wait_for_timeout(1500) # Wait for dialog to close
        #                 break
        #         except:
        #             continue
        # except Exception as e:
        #     print(f"No notifications dialog or couldn't handle it: {e}")
        
        # # Wait for home page to load - look for multiple possible indicators
        # home_loaded = False
        # for selector in ['svg[aria-label="Home"]', 'svg[aria-label="Direct"]', 'a[href="/explore/"]']:
        #     try:
        #         await page.wait_for_selector(selector, timeout=5000)
        #         home_loaded = True
        #         print(f"✅ Home page loaded, found indicator: {selector}")
        #         break
        #     except:
        #         continue
        
        # if not home_loaded:
        #     raise Exception("Could not confirm successful login to home page")
            
        # await page.screenshot(path="3_home_page.png")
        # print("✅ Screenshot saved: 3_home_page.png")
        # print("Successfully logged in!")
        
        # Step 2: Navigate to Direct Messages using CLICK method first
        print("\n📨 Directly navigating to Instagram DMs...")

    # Try direct navigation to inbox with appropriate wait time
    try:
        await page.goto("https://www.instagram.com/direct/inbox/", timeout=15000)
        await page.wait_for_load_state("networkidle", timeout=10000)
        print("✅ Navigated directly to inbox URL")

        # Check if we're on the DMs page and logged in
        is_logged_in = await page.evaluate('''
        () => {
            // Look for indicators that we're logged in and on DMs page
            return document.body.innerText.includes("Messages") || 
                document.querySelectorAll('div[aria-label="Chats"]').length > 0 ||
                document.querySelectorAll('div[role="listbox"]').length > 0;
        }
        ''')
        
        if is_logged_in:
            print("✅ Successfully logged in and accessed DMs")
        else:
            print("⚠️ On DMs page but login status unclear, proceeding anyway")
    except Exception as e:
        print(f"Direct navigation to inbox failed: {e}")
        
        # Fallback to mobile optimized URL
        try:
            print("Trying mobile view URL...")
            await page.goto("https://www.instagram.com/direct/inbox/?__d=y", timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=10000)
            print("✅ Navigated to mobile optimized inbox URL")
        except Exception as mobile_e:
            print(f"Mobile URL navigation failed: {mobile_e}")
            raise Exception("Could not navigate to DMs page after login")

    # Take screenshot of DM page
        await page.screenshot(path="3_dm_page.png")
        print("✅ Screenshot saved: 3_dm_page.png")
        # Check again for notification popup that might appear after navigation
        try:
            notification_button = await page.wait_for_selector('button:has-text("Not Now"), button:has-text("Not now")', timeout=2000)
            if notification_button:
                await notification_button.click()
                print("✅ Dismissed notification popup after navigation")
                await page.wait_for_timeout(1000)
        except:
            pass
            
        # Now take the screenshot
        await page.screenshot(path="4_messages_page.png")
        print("✅ Screenshot saved: 4_messages_page.png")
        
        # Step 3: Try to click on the first conversation to read messages
        print("\n📋 Attempting to access a conversation...")
        
        # Look for conversation elements that we can click on
        try:
            # Find and click on the first conversation in the list
            conversation_selectors = [
                'div[role="listitem"]',
                'div[role="row"]',
                'a[href*="/direct/t/"]',
                'div[data-testid="thread-item"]',
                'div.rOtsg',  # Instagram's CSS class for conversation items
                'div[style*="height"][role="button"]'  # Generic approach based on styling
            ]
            
            conversation_clicked = False
            
            for conv_selector in conversation_selectors:
                try:
                    conversations = await page.query_selector_all(conv_selector)
                    if conversations and len(conversations) > 0:
                        print(f"Found {len(conversations)} potential conversations with selector: {conv_selector}")
                        
                        # Click on the first conversation
                        await conversations[0].click()
                        print("✅ Clicked on first conversation")
                        await page.wait_for_timeout(3000)  # Wait for conversation to load
                        
                        # Check if URL changed (indicates successful click)
                        if '/direct/t/' in page.url:
                            print(f"✅ Successfully opened conversation: {page.url}")
                            conversation_clicked = True
                            break
                except Exception as click_error:
                    print(f"Error clicking conversation with selector {conv_selector}: {click_error}")
                    continue
                    
            if not conversation_clicked:
                print("⚠️ Could not click on any conversation")
        except Exception as e:
            print(f"Error trying to access conversations: {e}")
        
        # Replace both the multi-name version and the divit-specific version with this combined approach:

        # Try to find and click on specific conversations
        try:
            print("Looking for specific conversations...")
            
            # Define target usernames - ADD ALL YOUR TARGET USERNAMES HERE
            target_usernames = ["divit", "cheesepizzalover911", "rosescanbebluetoo", "S.A.M"]
            conversation_clicked = False
            
            # Loop through each username and try to find their conversations
            for username in target_usernames:
                print(f"👤 Looking for conversations with '{username}'...")
                
                # Use the SUCCESSFUL selector pattern that works for divit, but for each username
                conversation_selectors = [
                    # Based on the specific HTML structure that works
                    f'div.x9f619 div.x78zum5 span:has-text("{username}")',
                    f'div[class*="x9f619"] div[class*="x78zum5"] span:has-text("{username}")',
                    # More general selectors that might match conversation elements
                    f'span[dir="auto"]:has-text("{username}")',
                    f'div[role="listbox"] div span:has-text("{username}")'
                ]
                
                for selector in conversation_selectors:
                    try:
                        print(f"Trying selector: {selector}")
                        conversation = await page.wait_for_selector(selector, timeout=3000)
                        if conversation:
                            print(f"✅ Found conversation with selector: {selector} for {username}")
                            
                            # Click on the parent element that represents the whole conversation
                            await page.evaluate(f'''
                            (selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    // Find the clickable parent container (usually 3-4 levels up)
                                    let clickTarget = element;
                                    // Navigate up to find a suitable clickable container
                                    for (let i = 0; i < 4 && clickTarget; i++) {{
                                        if (clickTarget.tagName === 'DIV' && 
                                            (clickTarget.clientHeight > 40 && clickTarget.clientWidth > 200)) {{
                                            break;
                                        }}
                                        clickTarget = clickTarget.parentElement;
                                    }}
                                    
                                    if (clickTarget) {{
                                        console.log('Found click target for {username}:', clickTarget);
                                        clickTarget.click();
                                        return true;
                                    }}
                                }}
                                return false;
                            }}
                            ''', selector)
                            
                            print(f"✅ Clicked on conversation for {username}")
                            await page.wait_for_timeout(3000)  # Wait for conversation to load
                            
                            # Check if URL changed (indicates successful click)
                            if '/direct/t/' in page.url:
                                print(f"✅ Successfully opened conversation for {username}: {page.url}")
                                conversation_clicked = True
                                break
                    except Exception as e:
                        print(f"Error with selector {selector} for {username}: {e}")
                        continue
                
                # Break outer loop if we found and clicked any conversation
                if conversation_clicked:
                    print(f"✅ Successfully clicked on conversation for {username}")
                    break
                    
            if not conversation_clicked:
                print("⚠️ Could not click on any of the target usernames' conversations")

        except Exception as e:
            print(f"Error trying to click on conversations: {e}")
        
        # Add this code where you're trying to click on conversations

        # Try to find and click on a specific conversation
        try:
            print("Looking for specific conversations...")
            
            # Using the structure from the HTML you shared
            conversation_selectors = [
                # Based on the specific HTML structure you shared
                'div.x9f619 div.x78zum5 span:has-text("divit")',
                'div[class*="x9f619"] div[class*="x78zum5"] span:has-text("divit")',
                # More general selectors that might match conversation elements
                'span[dir="auto"]:has-text("divit")',
                'div[role="listbox"] div span:has-text("divit")'
            ]
            
            for selector in conversation_selectors:
                try:
                    print(f"Trying selector: {selector}")
                    conversation = await page.wait_for_selector(selector, timeout=3000)
                    if conversation:
                        print(f"✅ Found conversation with selector: {selector}")
                        # Click on the parent element that represents the whole conversation
                        await page.evaluate('''
                        (selector) => {
                            const element = document.querySelector(selector);
                            if (element) {
                                // Find the clickable parent container (usually 3-4 levels up)
                                let clickTarget = element;
                                // Navigate up to find a suitable clickable container
                                for (let i = 0; i < 4 && clickTarget; i++) {
                                    if (clickTarget.tagName === 'DIV' && 
                                        (clickTarget.clientHeight > 40 && clickTarget.clientWidth > 200)) {
                                        break;
                                    }
                                    clickTarget = clickTarget.parentElement;
                                }
                                
                                if (clickTarget) {
                                    console.log('Found click target:', clickTarget);
                                    clickTarget.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                        ''', selector)
                        
                        print("✅ Clicked on conversation")
                        await page.wait_for_timeout(3000)  # Wait for conversation to load
                        
                        # Check if URL changed (indicates successful click)
                        if '/direct/t/' in page.url:
                            print(f"✅ Successfully opened conversation: {page.url}")
                            break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
        except Exception as e:
            print(f"Error trying to click on conversations: {e}")
        
        # Take final screenshot of conversation (if we got there)
        await page.screenshot(path="5_conversation_page.png")
        print("✅ Screenshot saved: 5_conversation_page.png")
        
        # Step 4: Extract basic page info
        print("\n🔍 Analyzing current page...")
        page_info = await page.evaluate('''
        () => {
            return {
                url: window.location.href,
                title: document.title,
                text_length: document.body.innerText.length,
                has_dm_indicators: document.body.innerHTML.includes('inbox') || 
                                  document.body.innerHTML.includes('direct') ||
                                  document.body.innerHTML.includes('message'),
                has_conversation_view: window.location.href.includes('/direct/t/') ||
                                      document.body.innerHTML.includes('messageEntry')
            };
        }
        ''')
        
        # Create a simple report of what we found
        with open('instagram_dm_report.txt', 'w') as f:
            f.write("INSTAGRAM DM ACCESS REPORT\n")
            f.write("=========================\n\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Username: {INSTAGRAM_USERNAME}\n")
            f.write(f"Current URL: {page_info['url']}\n")
            f.write(f"Page Title: {page_info['title']}\n")
            f.write(f"Page Text Length: {page_info['text_length']} characters\n")
            f.write(f"DM Indicators Found: {'Yes' if page_info['has_dm_indicators'] else 'No'}\n")
            f.write(f"Conversation View: {'Yes' if page_info['has_conversation_view'] else 'No'}\n\n")
            
            # Extract any conversation elements on the page
            f.write("Page Analysis:\n")
            f.write("Check the screenshots to see your messages:\n")
            f.write("- 4_messages_page.png: Shows your DM inbox with all conversations\n")
            f.write("- 5_conversation_page.png: Shows an individual conversation if we could open one\n\n")
            f.write("Note: Instagram has protections against automated message extraction,\n")
            f.write("but you can see your messages in the screenshots.\n")
            
        print("\n📊 PAGE SUMMARY")
        print("=" * 50)
        print(f"URL: {page_info['url']}")
        print(f"Title: {page_info['title']}")
        print(f"DM Indicators Found: {'Yes' if page_info['has_dm_indicators'] else 'No'}")
        print(f"Opened Conversation: {'Yes' if page_info['has_conversation_view'] else 'No'}")
        print("=" * 50)
        
        print("\n✅ Process completed! Check screenshots to see your Instagram DMs.")
        print("📄 Report saved to instagram_dm_report.txt")
        
        # After taking screenshot of the DM page, add this enhanced message extraction code:

        print("\n📝 Attempting to extract message content...")
        
        # Enhanced conversation detection
        print("\n🔍 Using advanced methods to detect conversations...")
        
        conversation_data = await page.evaluate('''
        () => {
            // More aggressive approach to find conversation elements
            function findConversationElements() {
                // Store all potential conversation containers
                let candidates = [];
                
                // Method 1: Look for elements that contain both text and images (likely DM items)
                document.querySelectorAll('div').forEach(div => {
                    // Check if this might be a conversation item
                    if (div.clientHeight > 50 && div.clientHeight < 100 && 
                        div.clientWidth > 200 &&
                        div.querySelectorAll('img, svg').length &&
                        div.innerText.length > 10) {
                        candidates.push({
                            element: div,
                            score: 5,
                            text: div.innerText,
                            rect: div.getBoundingClientRect()
                        });
                    }
                });
                
                // Method 2: Find elements in the typical Instagram DM layout position
                const inboxContainer = document.querySelector('div[role="listbox"]') || 
                                      document.querySelector('div[aria-label*="inbox"]') ||
                                      document.querySelector('div[data-pagelet*="direct"]');
                
                if (inboxContainer) {
                    // Direct children are likely conversation items
                    inboxContainer.childNodes.forEach(child => {
                        if (child.nodeType === 1 && child.innerText) { // Element node with text
                            candidates.push({
                                element: child,
                                score: 10, // Higher score as this is more likely
                                text: child.innerText,
                                rect: child.getBoundingClientRect()
                            });
                        }
                    });
                }
                
                // Method 3: Find horizontally aligned elements that look like a list
                let potentialRows = [];
                document.querySelectorAll('div').forEach(div => {
                    const rect = div.getBoundingClientRect();
                    // Check if this might be a row in a list (width spans most of container, reasonable height)
                    if (rect.width > window.innerWidth * 0.5 && rect.height > 40 && rect.height < 120) {
                        potentialRows.push({
                            element: div,
                            y: rect.y,
                            height: rect.height,
                            text: div.innerText
                        });
                    }
                });
                
                // Find rows that are stacked vertically with consistent heights (likely a list)
                potentialRows.sort((a, b) => a.y - b.y);
                for (let i = 0; i < potentialRows.length - 1; i++) {
                    const current = potentialRows[i];
                    const next = potentialRows[i+1];
                    
                    // If rows are stacked and similar height, they're likely list items
                    if (Math.abs(current.height - next.height) < 20 && 
                        next.y - (current.y + current.height) < 20) {
                        candidates.push({
                            element: current.element,
                            score: 7,
                            text: current.text,
                            rect: current.element.getBoundingClientRect()
                        });
                    }
                });
                
                // Method 4: Look for avatar patterns (inbox items typically have avatars)
                document.querySelectorAll('img').forEach(img => {
                    const rect = img.getBoundingClientRect();
                    // Small, square images are likely avatars
                    if (rect.width > 20 && rect.width < 60 && 
                        Math.abs(rect.width - rect.height) < 5) {
                        // Find the parent container that might be a conversation item
                        let parent = img.parentElement;
                        for (let i = 0; i < 5 && parent; i++) { // Go up to 5 levels
                            if (parent.innerText && 
                                parent.clientWidth > window.innerWidth * 0.5 &&
                                parent.clientHeight > 40 && 
                                parent.clientHeight < 120) {
                                candidates.push({
                                    element: parent,
                                    score: 8, // Good indicator
                                    text: parent.innerText,
                                    rect: parent.getBoundingClientRect()
                                });
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                });
                
                // Extract meaning from conversation items
                return candidates.map(candidate => {
                    // Try to separate name from message text
                    const lines = candidate.text.split('\\n').filter(line => line.trim());
                    
                    // First line is often the username
                    const username = lines.length > 0 ? lines[0] : 'Unknown';
                    
                    // Other lines could be message preview, time, etc.
                    const preview = lines.length > 1 ? 
                                lines.slice(1).join(' ').trim() : '';
                    
                    // Look for time patterns
                    const timeMatch = candidate.text.match(/((\\d{1,2}:?\\d{2} ?[AP]M)|(a few|\\d+) (seconds|minutes|hours|days|weeks) ago|[Yy]esterday|[Tt]oday)/);
                    const timeText = timeMatch ? timeMatch[0] : '';
                    
                    // Check for unread indicators
                    const hasUnreadIndicator = 
                        candidate.element.querySelector('circle') !== null ||
                        candidate.element.innerHTML.includes('unread') ||
                        Boolean(candidate.element.querySelector('[style*="color:rgb(0, 149, 246)"]'));
                    
                    return {
                        full_text: candidate.text,
                        username: username,
                        preview: preview,
                        time: timeText,
                        score: candidate.score,
                        height: candidate.rect.height,
                        width: candidate.rect.width,
                        unread: hasUnreadIndicator
                    };
                }).filter(item => item.full_text.length > 0);
            }
            
            // Get page stats
            const pageTitle = document.title;
            const unreadMatch = pageTitle.match(/\\((\\d+)\\)/);
            const unreadCount = unreadMatch ? parseInt(unreadMatch[1]) : 0;
            
            // Execute the conversation finding function
            const allCandidates = findConversationElements();
            
            // Remove duplicates by comparing text content
            const uniqueTexts = new Set();
            const uniqueCandidates = allCandidates.filter(item => {
                if (uniqueTexts.has(item.full_text)) {
                    return false;
                }
                uniqueTexts.add(item.full_text);
                return true;
            });
            
            // Sort by score (higher score first)
            const sortedCandidates = uniqueCandidates.sort((a, b) => b.score - a.score);
            
            // Get the most likely conversations (highest scores)
            return {
                unread_count: unreadCount,
                all_candidates_count: allCandidates.length,
                unique_candidates_count: uniqueCandidates.length,
                conversations: sortedCandidates.slice(0, 10) // Return top 10 most likely conversations
            };
        }
        ''')
        
        # Create a visual map of the page for debugging
        print(f"Found {conversation_data.get('all_candidates_count', 0)} potential conversation elements")
        print(f"After filtering duplicates: {conversation_data.get('unique_candidates_count', 0)}")
        print(f"Unread count from page title: {conversation_data.get('unread_count', 0)}")
        
        # Save the conversation data to a detailed report
        conversations = conversation_data.get('conversations', [])
        
        with open('instagram_dm_text_report.txt', 'w') as f:
            f.write("INSTAGRAM DM TEXT REPORT\n")
            f.write("=======================\n\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Username: {INSTAGRAM_USERNAME}\n")
            f.write(f"Detected Conversations: {len(conversations)}\n")
            f.write(f"Unread Count: {conversation_data.get('unread_count', 0)}\n\n")
            
            if len(conversations) > 0:
                f.write("CONVERSATIONS (Sorted by likelihood):\n")
                f.write("----------------------------------\n\n")
                
                for i, conv in enumerate(conversations):
                    f.write(f"#{i+1}: {conv.get('username', 'Unknown')} ")
                    if conv.get('time'):
                        f.write(f"• {conv.get('time')} ")
                    f.write(f"[{'UNREAD' if conv.get('unread') else 'read'}]\n")
                    
                    if conv.get('preview'):
                        f.write(f"Message: {conv.get('preview')}\n")
                    else:
                        f.write(f"Full text: {conv.get('full_text')}\n")
                    
                    f.write(f"Confidence score: {conv.get('score')}/10\n\n")
            else:
                f.write("No conversations could be extracted.\n")
                f.write("This is likely due to Instagram's anti-scraping measures.\n")
                f.write("Please check the screenshot at 4_messages_page.png to view your messages.\n")
        
        # Show preview in console
        print("\n📨 CONVERSATION PREVIEW")
        print("=" * 50)
        
        if len(conversations) > 0:
            print(f"Found {len(conversations)} likely conversations")
            print(f"Unread Count: {conversation_data.get('unread_count', 0)}")
            print("=" * 50)
            
            # Show first few conversations
            for i, conv in enumerate(conversations[:3]):
                status = "UNREAD" if conv.get('unread') else "read"
                time_info = f" • {conv.get('time')}" if conv.get('time') else ""
                print(f"#{i+1}: {conv.get('username')}{time_info} [{status}]")
                print(f"Message: {conv.get('preview') or conv.get('full_text')}")
                print(f"Confidence: {conv.get('score')}/10")
                print("")
            
            if len(conversations) > 3:
                print(f"...and {len(conversations) - 3} more in the report")
        else:
            print("Could not extract conversation text")
            print("Please check the screenshot at 4_messages_page.png to see your messages")
        
        # Add this code after successfully clicking on a conversation:

        # If we got into a conversation, extract messages
        if '/direct/t/' in page.url:
            print("\n📄 Conversation opened - extracting messages...")
            
            # Take screenshot of conversation
            await page.screenshot(path="conversation_messages.png")
            print("✅ Screenshot saved: conversation_messages.png")
            
            # Try to extract message content
            message_data = await page.evaluate('''
            () => {
                // Find message elements
                const messages = [];
                
                // Method 1: Look for standard message containers
                document.querySelectorAll('div[role="row"]').forEach(row => {
                    if (row.innerText && row.innerText.length > 0) {
                        messages.push({
                            text: row.innerText,
                            is_mine: row.classList.contains('xdl72j9') || // Some Instagram classes for outgoing messages
                                   row.querySelector('[style*="margin-left: auto"]') !== null,
                            timestamp: null // We'll try to find this separately
                        });
                    }
                });
                
                // Method 2: Look for elements with certain structural hints
                const possibleMessages = [];
                document.querySelectorAll('div').forEach(div => {
                    // Message bubbles are often of medium height with reasonable width
                    if (div.clientHeight > 20 && div.clientHeight < 300 &&
                        div.clientWidth > 50 && div.clientWidth < 500 &&
                        div.innerText && div.innerText.length > 0) {
                        
                        // Check if has padding, borders or distinct background - typical for message bubbles
                        const style = window.getComputedStyle(div);
                        const hasStyle = style.padding !== '0px' || 
                                        style.border !== '' || 
                                        style.borderRadius !== '0px' ||
                                        style.background !== 'none';
                                        
                        if (hasStyle) {
                            possibleMessages.push({
                                element: div,
                                text: div.innerText,
                                score: 0 // Will calculate based on features
                            });
                        }
                    }
                });
                
                // Score possible messages based on features
                possibleMessages.forEach(msg => {
                    // Messages are often grouped by sender
                    if (msg.element.parentElement && 
                        msg.element.parentElement.childElementCount > 1) {
                        msg.score += 3;
                    }
                    
                    // Messages often have avatars nearby
                    if (msg.element.querySelector('img') || 
                        msg.element.parentElement.querySelector('img')) {
                        msg.score += 2;
                    }
                    
                    // Messages usually contain text that looks like a timestamp
                    if (msg.text.match(/\\d{1,2}:\\d{2}/) || 
                        msg.text.match(/yesterday|today|now|min|hour/i)) {
                        msg.score += 2;
                    }
                });
                
                // Add high-scoring messages to our list
                possibleMessages
                    .filter(msg => msg.score >= 3)
                    .forEach(msg => {
                        messages.push({
                            text: msg.text,
                            is_mine: msg.element.style.marginLeft === 'auto',
                            timestamp: null
                        });
                    });
                
                return {
                    url: window.location.href,
                    conversation_id: window.location.href.match(/\\/t\\/(.*?)(\\/|$)/)?.[1] || '',
                    message_count: messages.length,
                    messages: messages.slice(0, 50) // Limit to 50 messages
                };
            }
            ''');
            
            # Create a summary file for the conversation
            conversation_id = message_data.get('conversation_id', 'unknown')
            with open(f'conversation_{conversation_id}_summary.txt', 'w') as f:
                f.write("INSTAGRAM DM CONVERSATION SUMMARY\n")
                f.write("================================\n\n")
                f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Username: {INSTAGRAM_USERNAME}\n")
                f.write(f"Conversation URL: {message_data.get('url')}\n")
                f.write(f"Messages Found: {message_data.get('message_count', 0)}\n\n")
                
                messages = message_data.get('messages', [])
                if messages:
                    f.write("MESSAGES:\n")
                    f.write("--------\n\n")
                    
                    for i, msg in enumerate(messages):
                        sender = "Me" if msg.get('is_mine') else "Them"
                        timestamp = f" ({msg.get('timestamp')})" if msg.get('timestamp') else ""
                        f.write(f"{sender}{timestamp}: {msg.get('text')}\n\n")
                else:
                    f.write("No message content could be extracted.\n")
                    f.write("This is likely due to Instagram's protections against scraping.\n")
                    f.write("Please check the screenshot at conversation_messages.png\n")
            
            print(f"✅ Created message summary: conversation_{conversation_id}_summary.txt")
        
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