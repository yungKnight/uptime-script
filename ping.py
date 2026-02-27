import asyncio
import random
import string
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import datetime

def log_with_timestamp(message):
    """Print message with current timestamp and save to file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)  # Still print to terminal
    
    # Append to log file
    with open("ping-logs.txt", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def generate_random_name(length=None):
    """Generate a random 3-5 letter name with first letter capitalised"""
    if length is None:
        length = random.randint(3, 5)
    letters = random.choices(string.ascii_lowercase, k=length)
    letters[0] = letters[0].upper()
    return "".join(letters)

async def ping_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Changed to headless=True for proper Git Action workflow
        context = await browser.new_context()
        page = await browser.new_page()
        url = "https://edunalytica.onrender.com"
        
        log_with_timestamp(f"Navigating to {url}...")
        await page.goto(url, timeout=60000)
        log_with_timestamp("Waiting for app to wake...")
        await page.wait_for_load_state('networkidle')
        
        log_with_timestamp("App is now trying to boot up from sleep")
        
        # Keep trying until header is found or max attempts reached
        max_attempts = 3
        attempt = 1
        header = None
        
        while attempt <= max_attempts and header is None:
            log_with_timestamp(f"Attempt {attempt}/{max_attempts} to find header...")
            try:
                header = await page.wait_for_selector("h1#appName", timeout=10000)
                log_with_timestamp("Page is now online!")
                break
            except PlaywrightTimeoutError:
                if attempt < max_attempts:
                    log_with_timestamp(f"Header not found. Waiting 60 seconds before attempt {attempt + 1}...")
                    await asyncio.sleep(60)
                else:
                    log_with_timestamp("Max attempts reached. Site may be having issues.")
                attempt += 1

        # Only proceed with further checks if page came online
        if header is not None:
            # Assert 'summary' tag is present on the page
            log_with_timestamp("Checking for 'summary' tag on page...")
            try:
                summary_el = await page.wait_for_selector("summary", timeout=10000)
                log_with_timestamp("'summary' tag found on page. Clicking it...")
                await summary_el.click()
                log_with_timestamp("'summary' tag clicked successfully.")

                # Generate and type a random 3-5 letter name
                random_name = generate_random_name()
                log_with_timestamp(f"Generated random name: '{random_name}'. Typing into active field...")
                await page.keyboard.type(random_name)
                log_with_timestamp(f"Name '{random_name}' typed successfully.")

                # Click the submit button
                log_with_timestamp("Looking for 'button#submit'...")
                submit_btn = await page.wait_for_selector("button#submit", timeout=10000)
                log_with_timestamp("Submit button found. Clicking...")
                await submit_btn.click()
                log_with_timestamp("Submit button clicked. Form submitted successfully.")

                # Wait for page to settle after submit
                log_with_timestamp("Waiting for network idle after submit...")
                await page.wait_for_load_state('networkidle')
                log_with_timestamp("Network idle reached after submit.")

                # Assert '/Details' is in the current URL
                current_url = page.url
                log_with_timestamp(f"Current URL: {current_url}")
                if '/Details' in current_url:
                    log_with_timestamp("'/Details' found in URL. Proceeding...")

                    # Assert and click button.userDemo
                    log_with_timestamp("Looking for 'button.userDemo' on page...")
                    try:
                        user_demo_btn = await page.wait_for_selector("button.userDemo", timeout=10000)
                        log_with_timestamp("'button.userDemo' found. Clicking...")
                        await user_demo_btn.click()
                        log_with_timestamp("'button.userDemo' clicked successfully.")

                        # Wait for network idle after clicking userDemo
                        log_with_timestamp("Waiting for network idle after 'button.userDemo' click...")
                        await page.wait_for_load_state('networkidle')
                        log_with_timestamp("Network idle reached.")

                        # Assert 'analysis/results' is in the current URL
                        current_url = page.url
                        log_with_timestamp(f"Current URL: {current_url}")
                        if 'analysis/results' in current_url:
                            log_with_timestamp("'analysis/results' found in URL. Proceeding...")

                            # Assert and click button.btn
                            log_with_timestamp("Looking for 'button.btn' on page...")
                            try:
                                btn = await page.wait_for_selector("button.btn", timeout=10000)
                                log_with_timestamp("'button.btn' found. Clicking...")
                                await btn.click()
                                log_with_timestamp("'button.btn' clicked successfully.")

                                # Wait for network idle after clicking button.btn
                                log_with_timestamp("Waiting for network idle after 'button.btn' click...")
                                await page.wait_for_load_state('networkidle')
                                log_with_timestamp("Network idle reached.")

                                # Assert div[id*='visualizer-'] is present
                                log_with_timestamp("Looking for 'div[id*=\"visualizer-\"]' on page...")
                                try:
                                    visualizer = await page.wait_for_selector("div[id*='visualizer-']", timeout=10000)
                                    log_with_timestamp("SUCCESS: Visualizer element found on page. Full flow completed successfully!")
                                except PlaywrightTimeoutError:
                                    log_with_timestamp("Visualizer element not found within timeout. Flow may have stalled.")

                            except PlaywrightTimeoutError:
                                log_with_timestamp("'button.btn' not found on page within timeout. Skipping.")
                        else:
                            log_with_timestamp(f"'analysis/results' NOT found in URL: {current_url}. Skipping remaining steps.")

                    except PlaywrightTimeoutError:
                        log_with_timestamp("'button.userDemo' not found on page within timeout. Skipping.")
                else:
                    log_with_timestamp(f"'/Details' NOT found in URL: {current_url}. Skipping remaining steps.")

            except PlaywrightTimeoutError:
                log_with_timestamp("'summary' tag not found on page within timeout. Skipping interaction steps.")
        else:
            log_with_timestamp("Page did not come online. Skipping interaction steps.")
        
        await page.close()
        await browser.close()

asyncio.run(ping_site())