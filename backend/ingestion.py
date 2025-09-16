import os
import json
import asyncio
from urllib.parse import urlparse
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb
import feedparser

# Import the updated scraper
from scraper import Scraper

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)

# --- DATABASE SETUP ---
db_client = chromadb.PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="opportunities")

# --- DATA SOURCES ---
DATA_SOURCES = {
    "rss": [
        "https://www.digitalnewsasia.com/rss.xml"
    ],
    # "scrape": [
    #     "https://mdec.my/news",
    #     "https://www.jobstreet.com.my/en/internship-jobs",
    # ]
}

def get_ai_enrichment(content_text):
    """Uses Gemini to generate tags and an embedding for the given text."""
    print("Enriching content with AI...")
    tags = []
    embedding = None
    try:
        tag_model = genai.GenerativeModel('gemini-2.5-flash')
        tag_prompt = f"Read the following content and generate a JSON array of relevant tags (e.g., 'AI/ML', 'Grant', 'Internship', 'Cybersecurity'). Content: {content_text}"
        response = tag_model.generate_content(tag_prompt)
        
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        tags = json.loads(json_response)

        embedding_model = 'gemini-embedding-001'
        embedding_response = genai.embed_content(model=embedding_model, content=content_text)
        embedding = embedding_response['embedding']
        
    except Exception as e:
        print(f"Error during AI enrichment: {e}")
        return [], None
        
    return tags, embedding

def parse_rss(url):
    """Parses an RSS feed and returns a list of opportunities."""
    print(f"Parsing RSS feed: {url}")
    feed = feedparser.parse(url)
    opportunities = []
    for entry in feed.entries:
        opportunities.append({
            "title": entry.title,
            "link": entry.link,
            "description": entry.summary,
            "source": urlparse(url).netloc
        })
    return opportunities

async def main():
    """Main async function to run the entire data ingestion pipeline."""
    print("Starting data ingestion process...")
    try:
        rss_opportunities = []
        scraped_opportunities = []
        
        print("\n--- Processing RSS Feeds ---")
        for url in DATA_SOURCES["rss"]:
            rss_opportunities.extend(parse_rss(url))
        print(f"Found {len(rss_opportunities)} items from RSS feeds.")
            
        print("\n--- Processing Websites for Scraping ---")
        if "scrape" in DATA_SOURCES:
            for url in DATA_SOURCES["scrape"]:
                scraper_id = urlparse(url).netloc
                scraper = Scraper(id=scraper_id)
                scraped_results = await scraper.do_webscraping(start_url=url)

                if scraped_results:
                    print(f"Saving {len(scraped_results)} scraped pages to file...")
                    scraper.save_results_to_files(scraped_results)
                
                for result in scraped_results:
                    scraped_opportunities.append({
                        "title": result['title'],
                        "link": result['url'],
                        "description": result['summary'],
                        "source": scraper_id
                    })
            print(f"Found {len(scraped_opportunities)} items from scraping.")

        all_opportunities = rss_opportunities + scraped_opportunities
        print(f"\n--- Processing {len(all_opportunities)} Total Opportunities ---")
        
        if not all_opportunities:
            print("No new opportunities found. Exiting.")
            return

        for opp in all_opportunities:
            opp_id = opp.get("link")
            if not opp_id:
                print(f"Skipping opportunity with no link: {opp.get('title')}")
                continue

            existing = collection.get(ids=[opp_id])
            if existing['ids']:
                print(f"Skipping existing opportunity: {opp['title']}")
                continue

            print(f"\nProcessing new opportunity: {opp['title']}")
            content_to_enrich = f"Title: {opp['title']}\nDescription: {opp['description']}"
            
            tags, embedding = get_ai_enrichment(content_to_enrich)
            
            if not embedding:
                print(f"Skipping due to AI enrichment failure: {opp['title']}")
                continue
            
            collection.add(
                embeddings=[embedding],
                documents=[content_to_enrich],
                metadatas=[
                    {
                        "title": opp["title"],
                        "link": opp["link"],
                        "source": opp["source"],
                        "tags": ", ".join(tags)
                    }
                ],
                ids=[opp_id]
            )
            print(f"Successfully stored: {opp['title']}")

        print("\nData ingestion process finished successfully.")
    
    except Exception as e:
        print(f"\n--- A CRITICAL ERROR OCCURRED ---")
        print(f"An unexpected error stopped the ingestion process: {e}")
        import traceback
        traceback.print_exc()
        print("--- END OF ERROR ---")

if __name__ == '__main__':
    asyncio.run(main())