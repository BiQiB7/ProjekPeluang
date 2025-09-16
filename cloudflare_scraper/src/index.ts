import { launch, type BrowserWorker, type Browser, type Page } from "@cloudflare/playwright";

interface Env {
  MYBROWSER: BrowserWorker;
}

interface ScrapeResult {
  url: string;
  text: string;
  links: string[];
  scrapedSubPages?: ScrapeResult[];
}

async function scrapePage(
  browser: Browser,
  url: string,
  currentDepth: number,
  maxDepth: number,
  visited: Set<string>
): Promise<ScrapeResult | null> {
  if (currentDepth > maxDepth || visited.has(url)) {
    return null;
  }
  visited.add(url);

  let page: Page | null = null;
  try {
    console.log(`[${currentDepth}] Scraping: ${url}`);
    page = await browser.newPage();
    await page.goto(url, { waitUntil: "networkidle", timeout: 15000 });
    console.log(`[${currentDepth}] Successfully loaded: ${url}`);

    const pageData = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll("a")).map((a) => a.href);
      const text = document.body.innerText;
      return { text, links };
    });

    const result: ScrapeResult = {
      url,
      text: pageData.text,
      links: pageData.links,
    };

    if (currentDepth < maxDepth) {
      result.scrapedSubPages = [];
      // Scrape the first 3 valid, non-visited links to avoid excessive scraping
      const linksToScrape = pageData.links
        .filter((link) => link.startsWith("http") && !visited.has(link))
        .slice(0, 2);

      for (const link of linksToScrape) {
        const subPageResult = await scrapePage(browser, link, currentDepth + 1, maxDepth, visited);
        if (subPageResult) {
          result.scrapedSubPages.push(subPageResult);
        }
      }
    }

    return result;
  } catch (error) {
    console.error(`Error scraping ${url}:`, error);
    return {
      url,
      text: `Failed to scrape: ${error instanceof Error ? error.message : "Unknown error"}`,
      links: [],
    };
  } finally {
    if (page) {
      await page.close();
    }
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const scrapeUrl = url.searchParams.get("url");
    const depth = parseInt(url.searchParams.get("depth") || "1", 10);
    console.log(`Received request to scrape: ${scrapeUrl} with depth: ${depth}`);

    if (!scrapeUrl) {
      return new Response("Please provide a URL to scrape.", { status: 400 });
    }

    const browser = await launch(env.MYBROWSER);
    const visited = new Set<string>();
    try {
      const result = await scrapePage(browser, scrapeUrl, 1, depth, visited);
      return new Response(JSON.stringify(result, null, 2), {
        headers: { "Content-Type": "application/json" },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred";
      console.error("Error during scraping process:", errorMessage);
      return new Response(JSON.stringify({ error: "Failed to scrape the URL.", details: errorMessage }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    } finally {
      await browser.close();
    }
  },
};