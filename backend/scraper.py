import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import html2text
from playwright.async_api import async_playwright
import os
import json
from datetime import datetime

class Scraper:
    def __init__(self, id):
        self.id = id

    async def get_page_content(self, url, playwright):
        """Uses Playwright to get fully rendered HTML content from a system-installed browser."""
        # Using channel="chrome" tells Playwright to use the system-installed Google Chrome
        browser = await playwright.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page()
        try:
            # Increased timeout for potentially slow-loading pages
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            # Add a small delay to ensure dynamic content loads
            await page.wait_for_timeout(3000)
            content = await page.content()
            return content
        finally:
            await browser.close()

    async def do_webscraping(self, start_url, visited_urls=None, max_depth=2, visited_lock=None):
        if visited_urls is None:
            visited_urls = set()
        if visited_lock is None:
            visited_lock = asyncio.Lock()

        # Safety limits
        if len(visited_urls) >= 15:
            return []
        if max_depth <= 0:
            return []

        try:
            async with visited_lock:
                if start_url in visited_urls:
                    return []
                visited_urls.add(start_url)

            print(f"Scraping with System Chrome: {start_url}")

            async with async_playwright() as p:
                html_content = await self.get_page_content(start_url, p)

            if not html_content:
                return []

            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string.strip() if soup.title else "No title found"
            
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            clean_content = h.handle(html_content)

            current_result = {
                'url': start_url,
                'summary': clean_content,
                'title': title,
            }
            results = [current_result]

            base_domain = urlparse(start_url).netloc
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(start_url, href)
                if urlparse(absolute_url).netloc == base_domain:
                    if not any(ext in absolute_url for ext in ['.pdf', '.jpg', '.png', '#', '.zip', '.mailto:']):
                        links.append(absolute_url)

            tasks = []
            # Limit the number of links to follow per page
            for link in links[:5]:
                if link not in visited_urls:
                    task = self.do_webscraping(
                        link, 
                        visited_urls=visited_urls, 
                        max_depth=max_depth - 1,
                        visited_lock=visited_lock
                    )
                    tasks.append(task)
            
            if tasks:
                child_results = await asyncio.gather(*tasks, return_exceptions=True)
                for child_result in child_results:
                    if isinstance(child_result, list):
                        results.extend(child_result)

            return results

        except Exception as e:
            print(f"ERROR scraping {start_url}: {str(e)[:200]}...")
            return []

    def save_results_to_files(self, results):
        """Saves the raw scrape results to files for debugging."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base_directory = os.path.join(project_root, "DB", self.id)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        directory = os.path.join(base_directory, f"scrape_{timestamp}")
        os.makedirs(directory, exist_ok=True)
        
        json_file_path = os.path.join(directory, "scraping_results.json")
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"Saved raw scrape results to {json_file_path}")