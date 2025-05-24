import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import datetime

async def ping_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await browser.new_page()
        url = "https://edunalytica.onrender.com"
        
        print(f"Navigating to {url}...")
        await page.goto(url)
        print("Waiting for app to wake...")
        await page.wait_for_load_state('networkidle')
        
        print("App is now trying to boot up from sleep")
        
        # Keep trying until header is found or max attempts reached
        max_attempts = 3
        attempt = 1
        header = None
        
        while attempt <= max_attempts and header is None:
            print(f"Attempt {attempt}/{max_attempts} to find header...")
            try:
                header = await page.wait_for_selector("h1#appName", timeout=10000)
                print("Page is now online!")
                break
            except PlaywrightTimeoutError:
                if attempt < max_attempts:
                    print(f"Header not found. Waiting 60 seconds before attempt {attempt + 1}...")
                    await asyncio.sleep(60)
                else:
                    print("Max attempts reached. Site may be having issues.")
                attempt += 1
        
        await page.close()
        await browser.close()

asyncio.run(ping_site())