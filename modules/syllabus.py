import json
import os

DB_FILE = "isac_database.json"

def search_syllabus(query):
    """
    Searches ONLY the uploaded syllabus modules in the local database.
    This ensures students only learn what the Director/Tutor has uploaded.
    """
    if not query: return None
    
    # 1. Load the Database (Live Data)
    if not os.path.exists(DB_FILE):
        return None # No DB means no knowledge
        
    try:
        with open(DB_FILE, 'r') as f:
            db = json.load(f)
    except:
        return None

    # 2. Get the Uploaded Modules
    syllabus_modules = db.get('syllabus', [])
    
    if not syllabus_modules:
        return None # Director hasn't uploaded anything yet

    # 3. Search Logic
    query = query.lower()
    results = []
    
    for module in syllabus_modules:
        # We search in the Title, Summary, and Learning Objectives
        # (These fields come from the AI Ingest of the PDF)
        title = module.get('title', '').lower()
        summary = module.get('summary', '').lower()
        
        # Check for keyword match
        if query in title or query in summary:
            # Format the output for the ISAC Brain
            formatted_entry = f"""
            [SOURCE: {module.get('title')}]
            DIFFICULTY: {module.get('difficulty')}
            CONTENT_SUMMARY: {module.get('summary')}
            """
            results.append(formatted_entry)
            
    # Return the top 3 most relevant matches to keep context light
    return "\n\n".join(results[:3]) if results else None