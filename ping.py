import asyncio
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

async def ping_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Changed to headless=True for GitHub Actions
        context = await browser.new_context()
        page = await browser.new_page()
        url = "https://edunalytica.onrender.com"
        
        log_with_timestamp(f"Navigating to {url}...")
        await page.goto(url)
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
        
        await page.close()
        await browser.close()

asyncio.run(ping_site())