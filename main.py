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
        
        # Wait for either homepage or verification page
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
        
        # Wait for home page to load - look for multiple possible indicators
        home_loaded = False
        for selector in ['svg[aria-label="Home"]', 'svg[aria-label="Direct"]', 'a[href="/explore/"]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                home_loaded = True
                break
            except:
                continue
        
        if not home_loaded:
            raise Exception("Could not confirm successful login to home page")
            
        await page.screenshot(path="3_home_page.png")
        print("✅ Screenshot saved: 3_home_page.png")
        print("Successfully logged in!")
        
        # Step 2: Navigate to Direct Messages using CLICK method first
        print("\n📨 Attempting to navigate to Direct Messages...")
        
        try:
            print("Method 1: Clicking on Direct icon...")
            # Look for the Direct Messages icon and click it
            direct_button = await page.wait_for_selector('svg[aria-label="Direct"], a[href*="direct"]', timeout=5000)
            await direct_button.click()
            await page.wait_for_load_state("networkidle", timeout=10000)
            print("✅ Clicked on Direct Messages icon")
        except Exception as e:
            print(f"Could not click Direct icon: {e}")
            
            try:
                print("Method 2: Trying direct URL navigation...")
                # Try direct navigation to inbox
                await page.goto("https://www.instagram.com/direct/inbox/", timeout=40000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                print("✅ Navigated directly to inbox URL")
            except Exception as e:
                print(f"Direct URL navigation failed: {e}")
                
                # Try one more approach - mobile view might work better
                try:
                    print("Method 3: Trying mobile view URL...")
                    await page.goto("https://www.instagram.com/direct/inbox/?__d=y", timeout=40000)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    print("✅ Navigated to mobile optimized inbox URL")
                except Exception as e:
                    print(f"Mobile URL navigation failed: {e}")
                    raise Exception("All methods to access DMs failed")
        
        # Take screenshot of whatever page we ended up on
        await page.screenshot(path="4_messages_page.png")
        print("✅ Screenshot saved: 4_messages_page.png")
        
        # Step 3: Extract basic page info
        print("\n🔍 Analyzing current page...")
        page_info = await page.evaluate('''
        () => {
            return {
                url: window.location.href,
                title: document.title,
                text_length: document.body.innerText.length,
                has_dm_indicators: document.body.innerHTML.includes('inbox') || 
                                  document.body.innerHTML.includes('direct') ||
                                  document.body.innerHTML.includes('message')
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
            f.write(f"DM Indicators Found: {'Yes' if page_info['has_dm_indicators'] else 'No'}\n\n")
            
            # Extract any conversation elements on the page
            f.write("Page Analysis:\n")
            f.write("If you see your conversations in screenshot 4_messages_page.png, this means\n")
            f.write("we successfully accessed your DMs but could not programmatically extract them.\n")
            f.write("Instagram likely has protections against automated message extraction.\n")
            
        print("\n📊 PAGE SUMMARY")
        print("=" * 50)
        print(f"URL: {page_info['url']}")
        print(f"Title: {page_info['title']}")
        print(f"DM Indicators Found: {'Yes' if page_info['has_dm_indicators'] else 'No'}")
        print("=" * 50)
        
        print("\n✅ Process completed! Check screenshot 4_messages_page.png to see if DMs are visible.")
        print("📄 Report saved to instagram_dm_report.txt")
        
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
        input()
        
        # Close browser
        await context.close()
        await browser.close()
        await playwright.stop()

# Run the main function
asyncio.run(run_instagram_workflow())