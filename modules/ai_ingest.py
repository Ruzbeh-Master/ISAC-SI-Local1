import pypdf
import json
import google.generativeai as genai

# Hardcoded Key (As per your setup)
API_KEY = "AIzaSyB7CXelkxypu2x5-gjfKAbebI_0FhlczaA" 
try:
    genai.configure(api_key=API_KEY)
except:
    pass

def parse_pdf_content(file_obj):
    try:
        reader = pypdf.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except: return None

def ai_structure_syllabus(raw_text):
    if not API_KEY or "PASTE" in API_KEY: return []
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    Analyze this syllabus text. Break it into learning modules.
    Return JSON list: [{{ "id": "week_1", "title": "Topic Name", "summary": "...", "difficulty": "Beginner", "tags": ["Tag1"] }}]
    TEXT: {raw_text[:10000]}
    """
    try:
        res = model.generate_content(prompt).text
        clean_json = res.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except: return []