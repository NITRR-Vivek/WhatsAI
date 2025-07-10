"""
Trend Finder Agent - Fixed Version with Proper Async Handling

This agent finds the latest trending topics in Google Trends India:
https://trends.google.com/trending?geo=IN&hours=24&category=17
"""

from google.adk.agents import LlmAgent
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from datetime import datetime
import sys
import os
import threading
import concurrent.futures

# For Windows support
if sys.platform == "win32" and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"
TRENDS_URL = "https://trends.google.com/trending?geo=IN&hours=24&category=17"

# --- Scraper Function ---
async def scrape_trending_topics_async():
    """Async function to scrape trending topics"""
    EDGE_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.186"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=EDGE_UA,
            locale="en-US",
            extra_http_headers={
                "accept-language": "en-US,en;q=0.9",
                "referer": f"{urlparse(TRENDS_URL).scheme}://{urlparse(TRENDS_URL).netloc}"
            }
        )
        
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        page = await context.new_page()
        print(f"▶ Navigating to {TRENDS_URL}")
        await page.goto(TRENDS_URL, timeout=120000)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(5)

        try:
            # Try to get main content
            main_element = await page.query_selector("main")
            if main_element:
                main_text = await main_element.inner_text()
            else:
                main_text = await page.inner_text("body")

            # Split into lines
            lines = main_text.split('\n')
            lines = [line.strip() for line in lines if line.strip()]

            # Find index after "Sort by title"
            try:
                start_index = next(i for i, line in enumerate(lines) if "sort by title" in line.lower())
                end_index = next(i for i, line in enumerate(lines) if "rows per page" in line.lower())

                if start_index < end_index:
                    filtered_lines = lines[start_index:end_index]
                else:
                    filtered_lines = []
                print("⚠ 'Sort by title' appears after 'Rows per page'. Ignoring.")
            except StopIteration:
                print("⚠ 'Sort by title' or 'Rows per page' not found. Using full content.")
            
        except Exception as e:
            print(f"Text parsing failed: {e}")
        finally:
            await browser.close()

        return filtered_lines

def run_scraper_in_new_thread():
    """Run the scraper in a new thread with its own event loop"""
    def thread_target():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(scrape_trending_topics_async())
        except Exception as e:
            print(f"Error in thread_target: {e}")
            return []
        finally:
            loop.close()
    
    # Run in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(thread_target)
        try:
            return future.result(timeout=180)  # 3 minute timeout
        except concurrent.futures.TimeoutError:
            print("Scraping timed out")
            return []
        except Exception as e:
            print(f"Error in executor: {e}")
            return []

# --- Tool Function ---
def get_trending_topics() -> dict:
    """Fetch trending topics from Google Trends and return them as a dictionary"""
    print("Starting trending topics extraction...")
    
    try:
        topics = run_scraper_in_new_thread()
    except Exception as e:
        print(f"Error in get_trending_topics: {e}")
        topics = []
    
    # Fallback topics if scraping fails
    if not topics:
        print("Using fallback topics...")
        topics = []
    
    # Save topics to file for debugging
    try:
        os.makedirs("output", exist_ok=True)
        output_file = os.path.join("output", "trending_topics.txt")
        with open(output_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp}: {', '.join(topics)}\n")
        print(f"Topics saved to {output_file}")
    except Exception as file_error:
        print(f"Error writing to file: {file_error}")

    result = {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trending_topics": topics
    }
    
    print(f"Returning result: {result}")
    return result

# --- Trend Finder Agent ---
trend_finder_agent = LlmAgent(
    name="TrendFinderAgent",
    model=GEMINI_MODEL,
    instruction="""
You are a Trend Finder AI.

Your job is to find the top trending topics from Google Trends India by calling the `get_trending_topics` tool.

When you call the tool, you will receive a dictionary with 'trending_topics' that contains a list of topics.

IMPORTANT: You must return ONLY the list of trending topics as a clean, comma-separated string. 
Do NOT include any explanations, introductions, or formatting.
Do NOT include the timestamp or any other information.
Just return the topics separated by commas.

Example output format:
Cricket Match, Bollywood News, Stock Market, Weather Update, Technology News

After calling the tool, extract just the trending_topics list and format it as shown above.
""",
    description="Finds trending Google search topics from India",
    tools=[get_trending_topics],
    output_key="topics",
)