import json
import os
import base64
import time
from modules.knowledge_base import DEFAULT_KNOWLEDGE_BASE 

DB_FILE = "isac_database.json"

DEFAULT_DB = {
    "students": [
         {
             "name": "Student A", 
             "email": "student@mrdinstitute.com",
             "bio": "Engineering student.",
             "lci": {"overallScore": 0.5, "tier": "Medium", "accuracy": 0.5, "confidence": 0.5}, 
             "tier": "Medium", 
             "assignments": [], 
             "progress": {},
             "notifications": [],
             "skills": {}
         }
    ],
    "syllabus_docs": [],
    "syllabus_chapters": [],
    "chat_logs": {} # NEW: Stores chats by user_email
}

def init_db():
    if not os.path.exists(DB_FILE):
        data = DEFAULT_DB
    else:
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
        except:
            data = DEFAULT_DB
            
    # Self-Healing & Seeding
    if not data.get('syllabus_chapters'):
        data['syllabus_chapters'] = DEFAULT_KNOWLEDGE_BASE
    if 'chat_logs' not in data:
        data['chat_logs'] = {}
        
    save_db(data)
    return data

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- CHAT PERSISTENCE ---
def save_chat_session(user_email, session_data):
    """Saves a user's chat history to the DB."""
    db = init_db()
    if 'chat_logs' not in db: db['chat_logs'] = {}
    
    # Use email as key
    db['chat_logs'][user_email] = session_data
    save_db(db)

def load_chat_session(user_email):
    """Loads chat history for a user."""
    db = init_db()
    return db.get('chat_logs', {}).get(user_email, [{"id": "1", "title": "New Session", "msgs": []}])

# --- EXPORT DATA ---
def get_student_dataframe():
    """Returns a Pandas DataFrame of all students for exporting."""
    import pandas as pd
    db = init_db()
    
    export_data = []
    for s in db['students']:
        row = {
            "Name": s['name'],
            "Email": s.get('email', 'N/A'),
            "Tier": s.get('tier', 'Medium'),
            "LCI Score": s.get('lci', {}).get('overallScore', 0),
            "Modules Completed": len(s.get('progress', {})),
            "Risk Factor": "High" if s.get('lci', {}).get('overallScore', 0) < 0.4 else "Stable"
        }
        export_data.append(row)
    
    return pd.DataFrame(export_data)

# ... (Keep existing functions: update_student_profile, save_syllabus_document, etc.) ...
def update_student_profile(email, name, bio, password):
    db = init_db()
    for s in db['students']:
        if s.get('email', '').lower() == email.lower() or s['name'] == email:
            s['name'] = name
            s['bio'] = bio
            if password: s['password'] = password
            break
    save_db(db)

def save_syllabus_document(file_obj, uploaded_by="Director"):
    db = init_db()
    file_bytes = file_obj.getvalue()
    b64_data = base64.b64encode(file_bytes).decode('utf-8')
    size_mb = len(file_bytes) / (1024 * 1024)
    new_doc = {
        "id": f"doc_{int(time.time())}",
        "title": file_obj.name.split('.')[0],
        "fileName": file_obj.name,
        "fileType": "pdf" if file_obj.name.endswith(".pdf") else "word",
        "uploadDate": time.strftime("%Y-%m-%d"),
        "uploadedBy": uploaded_by,
        "size": f"{size_mb:.2f} MB",
        "data": b64_data
    }
    db['syllabus_docs'].insert(0, new_doc)
    save_db(db)
    return new_doc

def get_all_documents():
    return init_db().get('syllabus_docs', [])

def delete_document(doc_id):
    db = init_db()
    db['syllabus_docs'] = [d for d in db['syllabus_docs'] if d['id'] != doc_id]
    save_db(db)

def save_parsed_chapters(chapters):
    db = init_db()
    existing_titles = {c['title'] for c in db.get('syllabus_chapters', [])}
    count = 0
    for ch in chapters:
        if ch['title'] not in existing_titles:
            db['syllabus_chapters'].append(ch)
            count += 1
    save_db(db)
    return count

def assign_module_to_student(student_name, module_id):
    db = init_db()
    for s in db['students']:
        if s['name'] == student_name:
            if module_id not in s['assignments']:
                s['assignments'].append(module_id)
                if 'notifications' not in s: s['notifications'] = []
                s['notifications'].append({
                    "id": str(int(time.time())),
                    "title": "New Assignment",
                    "msg": f"You have been assigned module: {module_id}",
                    "read": False,
                    "date": time.strftime("%Y-%m-%d")
                })
            break
    save_db(db)