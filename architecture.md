# Personalized AI Opportunity Navigator - Architecture

This document outlines the architecture for the 1-week MVP of the Personalized AI Opportunity Navigator.

## Guiding Principles

- **Frictionless User Experience:** No accounts, no logins. Personalization is instant and persistent on the user's device.
- **Leverage Open Data:** Use a single, reliable open data source as the foundation for opportunities.
- **AI-Powered Enrichment:** Use Generative AI to add value to both the data and the user experience.
- **Serverless First:** Keep infrastructure management to a minimum by using serverless functions and managed services.
- **Rapid Prototyping:** The technology stack is chosen for speed of development.

## Technology Stack

- **Frontend:** Next.js on Vercel
- **Backend:** Python Web Server (e.g., Flask or FastAPI) hosted on AWS EC2.
- **Database:** Vector Database (e.g., ChromaDB, Supabase with pgvector). A vector-native database is chosen to handle both metadata filtering (for the MVP) and semantic search (for future features) in a single, elegant system.
- **AI:** OpenAI API

## High-Level Architecture

The system is composed of three main parts:

1.  **Data Ingestion Pipeline:** An automated, daily process that fetches data from an open data source, enriches it with AI-generated tags, and stores it in the database.
2.  **Frontend Application:** A Next.js application that provides the user interface. It handles the initial user profiling and displays the personalized feed.
3.  **AI Services:** A set of services that use the OpenAI API to tag content and create user profiles.

## Data Ingestion Strategy

Given the variety of data sources, we will adopt a two-pronged approach for data ingestion:

1.  **RSS Feed Parsing:** For sources with an RSS feed (e.g., Digital News Asia), a serverless function will periodically fetch the feed, parse the XML, and extract the relevant information. This is the most reliable and efficient method.
2.  **Web Scraping:** For sources without a structured feed (the majority of the list), we will use a web scraping solution. A serverless function will fetch the HTML of the target page and use a library like Cheerio (for Node.js) to parse the HTML and extract the data.

### Ingestion Process

The ingestion process will be a daily cron job that executes the following steps for each data source:

1.  **Fetch:** Get the raw data (XML for RSS, HTML for scraping).
2.  **Parse:** Extract the relevant fields (title, link, description, date).
3.  **Deduplicate:** Check if the opportunity already exists in the database (based on the link).
4.  **Enrich:** If it's a new opportunity, call an AI service to generate:
    -   A vector embedding of the opportunity's content.
    -   A list of metadata tags.
5.  **Store:** Save the opportunity's content, its vector embedding, and its metadata to the vector database.

### Data Model (Vector Database)

We will use a single vector database collection to store all opportunities. Each entry in the collection will consist of:

1.  **Vector Embedding:** A high-dimensional vector representing the semantic meaning of the opportunity's content.
2.  **Document/Content:** The raw text of the opportunity (title, description).
3.  **Metadata:** A JSON object containing structured data for filtering. This is the key to our MVP's functionality.

**Example Metadata:**

```json
{
  "link": "https://example.com/internship",
  "source": "MDEC",
  "published_date": "2023-10-27",
  "tags": ["AI/ML", "Internship", "Grant"],
  "opportunity_type": "Internship"
}
```

### Querying Strategy

-   **MVP (Personalized Feed):** The frontend will fetch opportunities by applying a metadata filter to the vector database, based on the tags stored in the user's `localStorage`. For example: `query(metadata_filter={"tags": {"$in": ["AI/ML", "Python"]}})`
-   **Future (RAG Chatbot):** The chatbot will perform a semantic search by converting the user's question into a vector and finding the most similar vectors in the database. It can also combine this with metadata filtering for more precise answers.

### Important Considerations for Scraping

-   **User-Agent:** Use a legitimate user-agent string to avoid being blocked.
-   **Rate Limiting:** Be respectful of the target sites and don't send too many requests in a short period.
-   **Selectors:** The HTML selectors used to extract data are brittle and may break if the website's layout changes. This is a known risk for a hackathon project.
-   **Headless Browser (Future):** For sites that render content with JavaScript, a headless browser like Puppeteer might be necessary. For the MVP, we will focus on sites that can be scraped with simple HTTP requests.

## Frontend and Personalization

The frontend is responsible for the user-facing experience.

1.  **"Stateless" Onboarding:**
    - On the first visit, a modal asks the user two questions: "What are you studying?" and "What's your dream career?".
    - The answers are stored in the browser's `localStorage`.
2.  **AI Profile Analyzer:**
    - When the user submits their answers, the frontend makes a call to a serverless function.
    - This function calls the OpenAI API with a prompt to generate a JSON array of relevant tags based on the user's profile.
    - The generated tags are then stored in the user's `localStorage`.
3.  **Personalized Feed:**
    - The main page fetches all recent opportunities from the Supabase database.
    - The frontend then uses the tags stored in `localStorage` to filter the opportunities on the client-side, showing only the most relevant items.
4.  **AI Transparency:** Each opportunity card will have a tooltip or badge indicating why it was recommended (e.g., "Recommended because you're interested in AI Engineering").

### Design Choice: AI-Generated Tags vs. Direct Semantic Search

For the MVP, we are choosing to use an AI model to translate the user's profile into a discrete set of tags for filtering, rather than using the user's raw input for a direct semantic search.

-   **Why?** This approach provides a more controlled and predictable user experience, which is crucial for a hackathon demo. It also directly enables the "AI Transparency" feature, allowing us to clearly explain to the user *why* they are seeing a particular opportunity.
-   **The AI Profile Analyzer as a "Refinement Layer":** This step acts as a powerful "query refinement" layer. It uses a sophisticated AI to turn a simple, high-level user profile into a precise, high-quality filter for the database, ensuring the relevance of the results.
-   **Future Evolution:** Direct semantic search is a powerful paradigm and the logical next step for the post-hackathon version of the application, especially for the RAG chatbot.

## API Contract

This section defines the API endpoints for the serverless functions.

### `POST /api/generate-profile-tags`

-   **Description:** Takes a user's study field and dream career and returns a list of AI-generated tags relevant to that profile.
-   **Request Body:**
    ```json
    {
      "studyField": "Computer Science",
      "dreamCareer": "AI Engineer"
    }
    ```
-   **Response Body (Success):**
    ```json
    {
      "tags": ["AI/ML", "Python", "Research", "Internship", "Data Science"]
    }
    ```
-   **Response Body (Error):**
    ```json
    {
      "error": "Failed to generate tags."
    }
    ```

### `GET /api/opportunities`

-   **Description:** Fetches a list of opportunities from the database, filtered by a list of tags. This is the core endpoint for building the personalized feed.
-   **Query Parameters:**
    -   `tags` (string, required): A comma-separated list of tags to filter by.
    -   **Example:** `/api/opportunities?tags=AI/ML,Python,Internship`
-   **Request Body:** None
-   **Response Body (Success):**
    ```json
    [
      {
        "id": "uuid-string",
        "title": "AI Research Internship",
        "link": "https://example.com/internship",
        "description": "An exciting internship opportunity...",
        "source": "University News",
        "published_date": "2023-10-27T10:00:00Z",
        "tags": ["AI/ML", "Research", "Internship"]
      }
    ]
    ```
-   **Response Body (Error):**
    ```json
    {
      "error": "Failed to fetch opportunities."
    }
    ```

### Outbound API Calls

#### OpenAI API - Content Tagger

-   **Endpoint:** `https://api.openai.com/v1/chat/completions`
-   **Method:** `POST`
-   **Prompt:** "Read the following text and generate a JSON array of relevant tags: [Opportunity Content]"

#### OpenAI API - Profile Analyzer

-   **Endpoint:** `https://api.openai.com/v1/chat/completions`
-   **Method:** `POST`
-   **Prompt:** "Based on a student interested in becoming a '[dreamCareer]' who is studying '[studyField]', what are the most relevant topics and opportunity types for them? Respond with a JSON array of tags."

## Future Plans (Post-Hackathon)

- **Gen AI-Powered Q&A (RAG Chatbot):** A chatbot that can answer user questions in a personalized way, using the user's profile to tailor the responses.
- **Persistent User Accounts:** Move from `localStorage` to a proper user authentication system and database to allow for cross-device access.
- **Multiple Data Sources:** Expand the data pipeline to include more data sources, such as web scrapers and other APIs.
- **Mentor Dashboards & Community Features:** Build out features to connect students with mentors and create a community.
- **The Career Roadmap:** Evolve the personalization into a more comprehensive, gamified career roadmap feature.

## Deliverables and Team Allocation

This section breaks down the required work into deliverables and allocates them to the two developers, Myra and BQ, based on their expertise.

### Myra (Web App & Mobile Expertise) - Frontend Owner

Myra will be responsible for the entire user-facing application.

-   **Deliverable 1: Frontend Setup:**
    -   Initialize a new Next.js project.
    -   Set up the basic project structure, styling (e.g., Tailwind CSS), and component library.
-   **Deliverable 2: Onboarding Modal:**
    -   Build the popup modal with the two questions ("What are you studying?", "What's your dream career?").
    -   Implement the logic to save the user's answers to the browser's `localStorage`.
-   **Deliverable 3: API Integration:**
    -   Implement the frontend logic to call the `POST /api/generate-profile-tags` endpoint when the user submits their profile.
    -   Implement the logic to call the `GET /api/opportunities` endpoint to fetch the personalized list of opportunities.
-   **Deliverable 4: Personalized Feed:**
    -   Build the main UI to display the opportunities as a list of cards.
    -   Implement the client-side filtering logic based on the tags retrieved from `localStorage`.
    -   Implement the "AI Transparency" tooltip feature on each card.

### BQ (Python for Gen AI Expertise) - Backend Owner

BQ will be responsible for the data pipeline and all backend services.

-   **Deliverable 1: EC2 Server & Database Setup:**
    -   Set up a Python web server framework (e.g., Flask or FastAPI) on the existing EC2 instance.
    -   Configure a process manager (e.g., Gunicorn) to run the web application.
    -   Set up and configure the vector database (e.g., a self-hosted ChromaDB instance on the same EC2 server, or a managed service).
-   **Deliverable 2: Data Ingestion Pipeline:**
    -   Write the Python scripts for web scraping and parsing RSS feeds.
    -   Implement the logic to connect to the OpenAI API to generate embeddings and metadata.
    -   Write the script to insert the data into the vector database.
    -   Configure a `cron` job on the EC2 instance to run this pipeline daily.
-   **Deliverable 3: API Endpoints:**
    -   Implement the `POST /api/generate-profile-tags` endpoint within the Flask/FastAPI application.
    -   Implement the `GET /api/opportunities` endpoint, including the logic to filter the vector database based on the `tags` query parameter.