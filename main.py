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
        # Add this new function after the popup check code:

        async def click_conversation_by_coordinates(page):
            """Click on the first conversation using a visual approach based on coordinates"""
            try:
                print("Attempting to click on conversation using visual coordinates...")
                
                # Take screenshot for debug
                await page.screenshot(path="before_click_coords.png")
                
                # Get page dimensions
                page_dimensions = await page.evaluate('''
                () => {
                    return {
                        width: window.innerWidth,
                        height: window.innerHeight
                    };
                }
                ''')
                
                # Define where conversations typically appear in the layout
                # These coordinates assume conversations are in left panel typically 1/3 of screen width
                panel_width = page_dimensions['width'] * 0.3
                
                # Define a grid of points to try clicking - left panel, multiple vertical positions
                click_points = [
                    # Format: [x, y, description]
                    [panel_width * 0.5, 150, "Top of conversation list"],
                    [panel_width * 0.5, 200, "Upper conversation"],
                    [panel_width * 0.5, 250, "Middle-upper conversation"],
                    [panel_width * 0.5, 300, "Middle conversation"],
                    [panel_width * 0.5, 350, "Middle-lower conversation"],
                    [panel_width * 0.5, 400, "Lower conversation"]
                ]
                
                # Try clicking each point until one works
                for x, y, description in click_points:
                    print(f"Trying to click at {x}, {y} ({description})...")
                    
                    # Use JavaScript click (more reliable than mouse)
                    clicked = await page.evaluate(f'''
                    () => {{
                        // Find the element at these coordinates
                        const element = document.elementFromPoint({x}, {y});
                        if (element) {{
                            // Check if this looks like a conversation
                            const isConversationItem = 
                                (element.innerText && element.innerText.length > 0) ||
                                element.querySelector('img') ||
                                element.parentElement.innerText ||
                                element.tagName === 'A' ||
                                element.role === 'row' ||
                                element.role === 'listitem';
                            
                            if (isConversationItem) {{
                                // Click it
                                element.click();
                                return true;
                            }}
                            
                            // If element itself isn't clickable, try to find a clickable parent
                            let parent = element.parentElement;
                            for (let i = 0; i < 4 && parent; i++) {{
                                if (parent.innerText && parent.innerText.length > 0) {{
                                    parent.click();
                                    return true;
                                }}
                                parent = parent.parentElement;
                            }}
                        }}
                        return false;
                    }}
                    ''')
                    
                    if clicked:
                        print(f"✅ Successfully clicked element at {x}, {y}")
                        # Wait for navigation
                        await page.wait_for_timeout(3000)
                        
                        # Check if URL changed
                        if '/direct/t/' in page.url:
                            print(f"✅ Successfully opened conversation: {page.url}")
                            return True
                    
                print("⚠️ Could not click any conversation by coordinates")
                return False
                
            except Exception as e:
                print(f"Error using coordinate-based clicking: {e}")
                return False

        # Wait a moment for any animations to complete
        await page.wait_for_timeout(1000)
        # Now take the screenshot
        await page.screenshot(path="4_messages_page.png")
        print("✅ Screenshot saved: 4_messages_page.png")
        
        # Continue with the rest of your navigation code...
        # Replace your current conversation click code with this multi-username version:

        print("\n👤 Searching for conversations with specific usernames...")

        # Define our target usernames - adjust as needed
        target_usernames = ["divit", "cheesepizzalover911", "rosescanbebluetoo", "S.A.M"]
        conversation_clicked = False

        # Try each username in sequence until one works
        for username in target_usernames:
            if conversation_clicked:
                break  # Stop once we've successfully opened one conversation
                
            print(f"Searching for conversation with '{username}'...")
            
            # Use the approach that worked for "divit" but for each username
            try:
                # This is the selector that worked for "divit", modify for each username
                username_selector = f'span:has-text("{username}")'
                
                # Use longer timeout to ensure we find the element
                conversation = await page.wait_for_selector(username_selector, timeout=5000)
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
                        conversation_clicked = True  # Important! Set this flag to indicate success
                        break  # Exit the username loop
                    else:
                        print(f"⚠️ Clicked on {username} but didn't navigate to conversation")
            except Exception as e:
                print(f"Could not find/click conversation with '{username}': {e}")

        # If we couldn't click any username conversation, try coordinates as last resort
        if not conversation_clicked:
            print("⚠️ Could not find any target conversations, trying coordinates...")
            try:
                # Try clicking at different coordinates where conversations might be
                for y_pos in [150, 200, 250, 300]:
                    await page.mouse.click(150, y_pos)
                    print(f"✅ Clicked at coordinates (150, {y_pos})")
                    await page.wait_for_timeout(2000)
                    
                    if '/direct/t/' in page.url:
                        print(f"✅ Coordinate click successfully opened conversation: {page.url}")
                        conversation_clicked = True
                        break
            except Exception as e:
                print(f"Coordinate clicking failed: {e}")

        # Take final screenshot of conversation (if we got there)
            await page.screenshot(path="5_conversation_page.png")
            print("✅ Screenshot saved: 5_conversation_page.png")

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
            
            # Add this code after successfully clicking on a conversation (after the screenshot)

            # Check if we successfully opened a conversation
            if '/direct/t/' in page.url:
                print("\n📝 Extracting conversation data...")
                
                # Extract basic page info first
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
                
                # Extract message data
                message_data = await page.evaluate('''
                () => {
                    // Try to find message elements
                    const messages = [];
                    
                    // Look for message containers
                    const messageElements = document.querySelectorAll('[role="row"], div[data-visualcompletion="ig-direct-message"], div.x78zum5 > div');
                    
                    // Extract text from any elements that look like messages
                    messageElements.forEach(el => {
                        if (el.innerText && el.innerText.trim().length > 0) {
                            // Try to determine if this is an outgoing message
                            const isOutgoing = el.getAttribute('style')?.includes('margin-left: auto') || 
                                              el.classList.contains('x11lhmoz') ||
                                              el.classList.contains('xdl72j9');
                            
                            messages.push({
                                text: el.innerText.trim(),
                                is_outgoing: isOutgoing || false,
                                html: el.innerHTML.substring(0, 100) // Include some HTML for debugging
                            });
                        }
                    });
                    
                    // If we couldn't find messages with the above selectors, try a more general approach
                    if (messages.length === 0) {
                        // Find elements that look like message bubbles based on styling and content
                        document.querySelectorAll('div').forEach(div => {
                            // Message bubbles are typically elements with reasonable dimensions and some text
                            if (div.clientHeight > 20 && div.clientHeight < 150 && 
                                div.clientWidth > 40 && div.clientWidth < 500 &&
                                div.innerText && div.innerText.trim().length > 0) {
                                
                                // Determine if likely a message by checking for certain styles
                                const computedStyle = window.getComputedStyle(div);
                                const hasBorderRadius = parseInt(computedStyle.borderRadius) > 3;
                                const hasPadding = parseInt(computedStyle.padding) > 0 || 
                                                  parseInt(computedStyle.paddingLeft) > 0;
                                
                                if (hasBorderRadius || hasPadding) {
                                    const isOutgoing = computedStyle.alignSelf === 'flex-end' || 
                                                    div.getAttribute('style')?.includes('margin-left: auto');
                                    
                                    messages.push({
                                        text: div.innerText.trim(),
                                        is_outgoing: isOutgoing || false,
                                        html: div.innerHTML.substring(0, 100)
                                    });
                                }
                            }
                        });
                    }
                    
                    // Remove likely duplicates (elements that contain exactly the same text)
                    const unique = [];
                    const seen = new Set();
                    messages.forEach(msg => {
                        if (!seen.has(msg.text)) {
                            seen.add(msg.text);
                            unique.push(msg);
                        }
                    });
                    
                    return {
                        count: unique.length,
                        messages: unique.slice(0, 50)  // Limit to 50 messages
                    };
                }
                ''')
                
                # Now create a detailed report with conversation data
                import time
                report_filename = "instagram_dm_report.txt"
                
                with open(report_filename, 'w', encoding='utf-8') as report:
                    report.write("INSTAGRAM DM ACCESS REPORT\n")
                    report.write("=========================\n\n")
                    report.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    report.write(f"Username: {os.environ.get('INSTAGRAM_USERNAME')}\n")
                    report.write(f"Current URL: {page_info.get('url', 'Unknown')}\n")
                    report.write(f"Page Title: {page_info.get('title', 'Unknown')}\n")
                    report.write(f"Page Text Length: {page_info.get('text_length', 0)} characters\n")
                    report.write(f"DM Indicators Found: {'Yes' if page_info.get('has_dm_indicators', False) else 'No'}\n")
                    report.write(f"Conversation View: {'Yes' if page_info.get('has_conversation_view', False) else 'No'}\n\n")
                    
                    # Add message content if we found any
                    message_count = message_data.get('count', 0)
                    messages = message_data.get('messages', [])
                    
                    if message_count > 0:
                        report.write(f"CONVERSATION MESSAGES ({message_count} found)\n")
                        report.write("============================\n\n")
                        
                        for idx, msg in enumerate(messages):
                            sender = "You" if msg.get('is_outgoing') else "Them"
                            report.write(f"[{idx+1}] {sender}: {msg.get('text')}\n\n")
                    else:
                        report.write("MESSAGES\n")
                        report.write("========\n\n")
                        report.write("No individual messages could be extracted.\n")
                        report.write("Instagram has protections against automated message extraction.\n")
                        report.write("Check the screenshots to see your messages:\n")
                        report.write("- 4_messages_page.png: Shows your DM inbox with all conversations\n")
                        report.write("- 5_conversation_page.png: Shows this specific conversation\n")
                    
                print(f"✅ DM report saved to {report_filename}")

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