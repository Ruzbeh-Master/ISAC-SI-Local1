import pypdf
import json
import google.generativeai as genai

# Hardcoded Key (As per your setup)
API_KEY = "AIzaSyDSrTS27xN2wqPa4Byt8-dOwXwY2RYBE20" 
genai.configure(api_key=API_KEY)

def parse_pdf_content(file_obj):
    """Extracts text from PDF object"""
    try:
        reader = pypdf.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return None

def ai_structure_syllabus(raw_text):
    """Uses Gemini to break text into chapters (The Knowledge Base)"""
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
    Analyze this syllabus text. Break it into learning modules.
    Return JSON list: [{{ "id": "week_1", "title": "Topic Name", "summary": "...", "difficulty": "Beginner" }}]
    
    TEXT: {raw_text[:15000]}
    """
    
    try:
        res = model.generate_content(prompt).text
        clean_json = res.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return []