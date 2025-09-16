import os
import json
import subprocess
import sys
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)

TRIGGER_SECRET_KEY = os.getenv("TRIGGER_SECRET_KEY")
if not TRIGGER_SECRET_KEY:
    raise ValueError("TRIGGER_SECRET_KEY not found in environment variables.")

# --- DATABASE CLIENT ---
db_client = chromadb.PersistentClient(path="./chroma_db")
collection = db_client.get_or_create_collection(name="opportunities")

# --- FLASK APP ---
app = Flask(__name__)

@app.route('/api/generate-profile-tags', methods=['POST'])
def generate_profile_tags():
    """
    Takes a user's study field and dream career and returns a list of
    AI-generated tags relevant to that profile.
    """
    data = request.get_json()
    if not data or 'studyField' not in data or 'dreamCareer' not in data:
        return jsonify({"error": "Missing studyField or dreamCareer"}), 400

    study_field = data['studyField']
    dream_career = data['dreamCareer']
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (f"Based on a student interested in becoming a '{dream_career}' who is studying "
                  f"'{study_field}', what are the most relevant topics and opportunity types for them? "
                  f"Respond with a JSON array of tags.")
        
        response = model.generate_content(prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        tags = json.loads(json_response)
        
        return jsonify({"tags": tags})
        
    except Exception as e:
        print(f"Error generating profile tags: {e}")
        return jsonify({"error": "Failed to generate tags from AI."}), 500

@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """
    Fetches a list of opportunities from the database, filtered by tags.
    """
    tags_param = request.args.get('tags')
    if not tags_param:
        return jsonify({"error": "Missing 'tags' query parameter"}), 400

    tag_list = [tag.strip() for tag in tags_param.split(',')]
    
    # Construct a metadata filter for ChromaDB.
    # This creates a filter that finds documents where the 'tags' metadata field
    # contains any of the tags in tag_list.
    where_filter = {
        "$or": [
            {"tags": {"$contains": tag}} for tag in tag_list
        ]
    }
    
    try:
        results = collection.get(
            where=where_filter,
            include=["metadatas", "documents"] 
        )
        
        # Format the results to match the API contract
        formatted_results = []
        for i, metadata in enumerate(results['metadatas']):
            formatted_results.append({
                "id": results['ids'][i],
                "title": metadata.get("title"),
                "link": metadata.get("link"),
                "description": results['documents'][i],
                "source": metadata.get("source"),
                "tags": metadata.get("tags", "").split(", ")
            })
            
        return jsonify(formatted_results)

    except Exception as e:
        print(f"Error querying database: {e}")
        return jsonify({"error": "Failed to retrieve opportunities."}), 500

@app.route('/api/trigger-ingestion', methods=['POST'])
def trigger_ingestion():
    """
    Manually triggers the data ingestion pipeline as a background process.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or f"Bearer {TRIGGER_SECRET_KEY}" != auth_header:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get the path to the python executable that is running the app
        python_executable = sys.executable
        script_path = os.path.join(os.path.dirname(__file__), 'ingestion.py')
        
        # Define log files for the subprocess output
        log_file_path = os.path.join(os.path.dirname(__file__), 'ingestion.log')
        err_file_path = os.path.join(os.path.dirname(__file__), 'ingestion.err')

        # Open the log files
        log_file = open(log_file_path, 'w')
        err_file = open(err_file_path, 'w')

        # Run ingestion.py as a non-blocking background process, redirecting output
        subprocess.Popen([python_executable, script_path], stdout=log_file, stderr=err_file)
        
        print("Manual ingestion triggered. Check ingestion.log for progress.")
        return jsonify({
            "status": "Ingestion process started.",
            "log_file": log_file_path,
            "error_log_file": err_file_path
        })
        
    except Exception as e:
        print(f"Error triggering ingestion: {e}")
        return jsonify({"error": "Failed to start ingestion process."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)