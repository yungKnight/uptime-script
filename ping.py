import asyncio
import argparse
import random
import string
import logging
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("ping-logs.txt")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)

def generate_random_name(length=None):
    """Generate a random 3-5 letter name with first letter capitalised"""
    if length is None:
        length = random.randint(3, 5)
    letters = random.choices(string.ascii_lowercase, k=length)
    letters[0] = letters[0].upper()
    return "".join(letters)

async def ping_site(record=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Set up context with video recording if --record flag is passed
        context_options = {}
        if record:
            context_options["record_video_dir"] = "."
            context_options["record_video_size"] = {"width": 1280, "height": 720}
            logger.info("Video recording enabled. Will save to 'ping-run.mp4'.")

        context = await browser.new_context(**context_options)
        page = await context.new_page()
        url = "https://edunalytica.onrender.com"

        # Retry goto up to 3 times in case the site is slow to respond
        max_goto_attempts = 3
        for goto_attempt in range(1, max_goto_attempts + 1):
            try:
                logger.info(f"Navigating to {url} (attempt {goto_attempt}/{max_goto_attempts})...")
                await page.goto(url, timeout=60000)
                logger.info("Navigation successful.")
                break
            except (PlaywrightTimeoutError, PlaywrightError) as e:
                if goto_attempt < max_goto_attempts:
                    logger.warning(f"Navigation failed: {e.__class__.__name__} — {str(e).splitlines()[0]}. Retrying in 15 seconds...")
                    await asyncio.sleep(15)
                else:
                    logger.error(f"Navigation failed after all {max_goto_attempts} attempts. Exiting.")
                    await browser.close()
                    return

        logger.info("Waiting for app to wake...")
        await page.wait_for_load_state('networkidle')

        logger.info("App is now trying to boot up from sleep.")

        # Keep trying until header is found or max attempts reached
        max_attempts = 3
        attempt = 1
        header = None

        while attempt <= max_attempts and header is None:
            logger.debug(f"Asserting h1#appName presence (attempt {attempt}/{max_attempts})...")
            try:
                header = await page.wait_for_selector("h1#appName", timeout=10000)
                logger.info("Page is now online!")
                break
            except PlaywrightTimeoutError:
                if attempt < max_attempts:
                    logger.warning(f"h1#appName not found. Waiting 60 seconds before attempt {attempt + 1}...")
                    await asyncio.sleep(60)
                else:
                    logger.error("Max attempts reached. h1#appName never appeared. Site may be having issues.")
                attempt += 1

        if header is not None:
            # Assert 'summary' tag is present on the page
            logger.debug("Asserting 'summary' tag is present on page...")
            try:
                summary_el = await page.wait_for_selector("summary", timeout=10000)
                logger.info("'summary' tag found. Clicking...")
                await summary_el.click()
                logger.info("'summary' tag clicked successfully.")

                # Generate and type a random 3-5 letter name
                random_name = generate_random_name()
                logger.info(f"Generated random name: '{random_name}'. Typing into active field...")
                await page.keyboard.type(random_name)
                logger.info(f"Name '{random_name}' typed successfully.")

                # Click the submit button
                logger.debug("Asserting 'button#submit' is present on page...")
                submit_btn = await page.wait_for_selector("button#submit", timeout=10000)
                logger.info("Submit button found. Clicking...")
                await submit_btn.click()
                logger.info("Submit button clicked. Form submitted successfully.")

                logger.info("Waiting for network idle after submit...")
                await page.wait_for_url("**/Details**", timeout=10000)
                await page.wait_for_load_state("networkidle")
                logger.info("Network idle reached after submit.")

                # Assert '/Details' is in the current URL
                current_url = page.url
                logger.debug(f"Asserting '/Details' in current URL: {current_url}")
                if '/Details' in current_url:
                    logger.info("'/Details' confirmed in URL. Proceeding...")

                    # Assert and click button.userDemo
                    logger.debug("Asserting 'button.userDemo' is present on page...")
                    try:
                        user_demo_btn = await page.wait_for_selector("button.userDemo", timeout=10000)
                        logger.info("'button.userDemo' found. Clicking...")
                        await user_demo_btn.click()
                        logger.info("'button.userDemo' clicked successfully.")

                        # Wait for network idle after clicking userDemo
                        logger.info("Waiting for network idle after 'button.userDemo' click...")
                        try:
                            await page.wait_for_url("**analysis/results**", timeout=15000)
                            await page.wait_for_load_state("networkidle")
                            logger.info("Network idle reached.")
                        except PlaywrightTimeoutError:
                            logger.error("Timed out waiting for 'analysis/results' URL.")

                        # Assert 'analysis/results' is in the current URL
                        current_url = page.url
                        logger.debug(f"Asserting 'analysis/results' in current URL: {current_url}")
                        if 'analysis/results' in current_url:
                            logger.info("'analysis/results' confirmed in URL. Proceeding...")

                            # Assert and click button.btn
                            logger.debug("Asserting 'button.btn' is present on page...")
                            try:
                                btn = await page.wait_for_selector("button.btn", timeout=10000)
                                logger.info("'button.btn' found. Clicking...")
                                await btn.click()
                                logger.info("'button.btn' clicked successfully.")

                                # Wait for network idle after clicking button.btn
                                logger.info("Waiting for network idle after 'button.btn' click...")
                                await page.wait_for_load_state('load')
                                logger.info("Page elements are fully loaded in page.")

                                # Assert div[id*='visualizer-'] is visible
                                logger.debug("Asserting 'div[id*=\"visualizer-\"]' is visible on page...")
                                try:
                                    visualizer = await page.wait_for_selector("div[id*='visualizer-']", state='visible', timeout=10000)
                                    logger.info("SUCCESS: Visualizer element visible on page. Full flow completed successfully!")
                                except PlaywrightTimeoutError:
                                    logger.error("Visualizer element not visible within timeout. Flow may have stalled.")

                            except PlaywrightTimeoutError:
                                logger.error("'button.btn' not found on page within timeout.")
                        else:
                            logger.error(f"'analysis/results' NOT found in URL: {current_url}. Aborting remaining steps.")

                    except PlaywrightTimeoutError:
                        logger.error("'button.userDemo' not found on page within timeout.")
                else:
                    logger.error(f"'/Details' NOT found in URL: {current_url}. Aborting remaining steps.")

            except PlaywrightTimeoutError:
                logger.error("'summary' tag not found on page within timeout. Skipping interaction steps.")
        else:
            logger.error("Page did not come online. Skipping interaction steps.")

        if record:
            video_path = await page.video.path()

        await page.close()

        if record:
            await context.close()
            await browser.close()
            await asyncio.sleep(1)
            if os.path.exists("ping-run.mp4"):
                os.remove("ping-run.mp4")
            os.rename(video_path, "ping-run.mp4")

            logger.info("Video saved as 'ping-run.mp4'.")
        else:
            await context.close()
            await browser.close()

parser = argparse.ArgumentParser()
parser.add_argument("--record", action="store_true", help="Record the session as ping-run.mp4")
args = parser.parse_args()

asyncio.run(ping_site(record=args.record))