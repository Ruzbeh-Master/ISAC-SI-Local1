import json
import os
import base64
import time
from modules.knowledge_base import DEFAULT_KNOWLEDGE_BASE 

DB_FILE = "isac_database.json"

# Default DB with correct structure
DEFAULT_DB = {
    "students": [
         {
             "name": "Student A", 
             "email": "student@mrdinstitute.com",
             "bio": "Engineering student passionate about EVs.",
             "lci": {
                 "overallScore": 0.5,
                 "tier": "Medium",
                 "accuracy": 0.5,
                 "confidence": 0.5
             }, 
             "tier": "Medium", 
             "assignments": [], 
             "progress": {}, # Format: {"week_1": 85, "week_2": 90}
             "notifications": []
         }
    ],
    "syllabus_docs": [],
    "syllabus_chapters": [] 
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
            
    # --- SELF-HEALING: Fix LCI Format ---
    for s in data['students']:
        # If LCI is a number (old format), convert to object
        if isinstance(s.get('lci'), (float, int)):
            old_score = float(s['lci'])
            s['lci'] = {
                "overallScore": old_score,
                "tier": s.get('tier', "Medium"),
                "accuracy": old_score, 
                "confidence": old_score
            }
            
    # --- SEED DATA: Load Full Knowledge Base ---
    if not data.get('syllabus_chapters'):
        data['syllabus_chapters'] = DEFAULT_KNOWLEDGE_BASE
        
    # Save repairs/seeds
    save_db(data)
    return data

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def update_student_profile(email, name, bio, password):
    db = init_db()
    for s in db['students']:
        if s.get('email', '').lower() == email.lower() or s['name'] == email: # Fallback for old names
            s['name'] = name
            s['bio'] = bio
            if password: s['password'] = password # In real app, hash this!
            break
    save_db(db)
    return True

# ... (Keep save_syllabus_document, get_all_documents, delete_document, save_parsed_chapters, assign_module_to_student from previous steps) ...
# Ensure you copy them here or keep them if you are editing the file.
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