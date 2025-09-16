import asyncio
import sys
from urllib.parse import urlparse
from scraper import Scraper
import json

async def test_single_url(url_to_test):
    """
    A standalone script to test the Playwright scraper on a single URL.
    """
    print(f"--- Starting standalone scrape test for: {url_to_test} ---")
    
    # The scraper ID is just for creating a directory, so we'll derive it
    scraper_id = urlparse(url_to_test).netloc
    scraper = Scraper(id=scraper_id)
    
    # Run the scraping process
    results = await scraper.do_webscraping(start_url=url_to_test)
    
    if not results:
        print("\n--- Test Finished: No results were scraped. ---")
        print("This could be due to an error or an empty page.")
        return

    print(f"\n--- Test Finished: Successfully scraped {len(results)} page(s). ---")
    
    # Save the results to a file for inspection
    scraper.save_results_to_files(results)
    
    print("\n--- Scraped Content Summary ---")
    for i, result in enumerate(results):
        print(f"\n--- Page {i+1} ---")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        # Print the first 300 characters of the summary
        print(f"Summary (first 300 chars): \n{result['summary'][:300]}...")
    
    print("\nFull results have been saved to the DB/ directory for inspection.")

if __name__ == '__main__':
    # Check if a URL was provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python3 test_scraper.py <URL_TO_TEST>")
        print("Example: python3 test_scraper.py https://mdec.my/news")
        sys.exit(1)
        
    url = sys.argv[1]
    asyncio.run(test_single_url(url))