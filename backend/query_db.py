import chromadb
import json

def query_all_data():
    """
    Connects to the ChromaDB and retrieves all entries from the 'opportunities' collection.
    """
    print("Connecting to the database at './chroma_db'...")
    
    try:
        # Connect to the same persistent database
        db_client = chromadb.PersistentClient(path="backend/chroma_db")
        
        # Get or create the collection. This is safer and won't fail if the DB is empty.
        collection = db_client.get_or_create_collection(name="opportunities")
        
        count = collection.count()
        if count == 0:
            print("The 'opportunities' collection exists, but it is empty.")
            print("Please run the ingestion script first by calling the /api/trigger-ingestion endpoint.")
            return

        print(f"Found collection with {count} items.")
        
        # Get all items in the collection.
        # You can limit the results, e.g., limit=10
        all_items = collection.get(include=["metadatas", "documents"])
        
        print("\n--- All Items in Database ---")
        
        # Pretty print the results
        for i in range(len(all_items['ids'])):
            print("-" * 40)
            print(f"ID: {all_items['ids'][i]}")
            print("Metadata:")
            print(json.dumps(all_items['metadatas'][i], indent=2))
            print("\nDocument Content:")
            print(all_items['documents'][i])
            print("-" * 40)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Have you run the ingestion script yet to create the database?")

if __name__ == "__main__":
    query_all_data()