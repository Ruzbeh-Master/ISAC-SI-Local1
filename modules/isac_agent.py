import google.generativeai as genai
import streamlit as st
import json
import random
from PIL import Image

# Safety Import
try:
    from modules.syllabus import search_syllabus
except ImportError:
    def search_syllabus(q): return None

class ISACDualAgent:
    def __init__(self):
        # HARDCODED KEY
        self.google_key = "AIzaSyDSrTS27xN2wqPa4Byt8-dOwXwY2RYBE20" 
        
        if self.google_key:
            genai.configure(api_key=self.google_key)
            self.fast_brain = genai.GenerativeModel('gemini-flash-latest') 

    def determine_layer(self, query):
        q = query.lower()
        if any(x in q for x in ['quiz', 'test', 'score', 'grade']): return "Assessment"
        if any(x in q for x in ['why', 'how', 'explain', 'concept']): return "Cognitive"
        if any(x in q for x in ['plan', 'schedule', 'next', 'track']): return "Optimization"
        if any(x in q for x in ['help', 'hello', 'hi', 'thanks']): return "Engagement"
        return "Operational"

    def process_query(self, user_query, student_name, student_tier, attachment=None):
        if not self.google_key:
            return {"response": "System Offline", "active_layer": "Operational", "grounding": []}

        # 1. Determine Layer
        active_layer = self.determine_layer(user_query)

        # 2. Check Syllabus (Text Only)
        syllabus_context = search_syllabus(user_query)
        context_msg = f"CONTEXT: {syllabus_context}" if syllabus_context else ""

        # 3. Prepare Input for Gemini
        # Gemini Flash supports [text, image] lists natively
        prompt_text = f"""
        You are ISAC, a Synthetic Intelligence Tutor.
        Student: {student_name} (Tier: {student_tier}).
        Active Layer: {active_layer}
        {context_msg}
        
        User Query: "{user_query}"
        
        Task: Answer the user. If an image is provided, analyze it technically.
        """
        
        inputs = [prompt_text]
        if attachment:
            inputs.append(attachment) # Add image/file object

        try:
            response = self.fast_brain.generate_content(inputs)
            response_text = response.text
        except Exception as e:
            response_text = f"I encountered a neural processing error: {str(e)}"

        # 4. Grounding
        grounding = []
        if syllabus_context:
            grounding.append({"title": "Internal Syllabus DB", "uri": "#syllabus"})
        
        return {
            "response": response_text,
            "active_layer": active_layer,
            "grounding_sources": grounding
        }

    # --- NEW: Smart Recommendations (Matching StudentDashboard.tsx) ---
    def get_recommendations(self, student_data, all_modules):
        """
        Replicates the logic from StudentDashboard.tsx
        """
        recs = []
        
        # --- FIX: ROBUST LCI CHECK ---
        lci_data = student_data.get('lci', {})
        
        # Check if lci is just a number (Old DB format) vs Object (New format)
        if isinstance(lci_data, (float, int)):
            # If it's a float, the 'tier' is likely stored at the student level
            tier = student_data.get('tier', 'Medium')
        else:
            # If it's a dictionary, get tier from inside it
            tier = lci_data.get('tier', 'Medium')
        # -----------------------------
        
        # 1. Growth (Based on Tier)
        unassigned = [m for m in all_modules if m['id'] not in student_data.get('assignments', [])]
        
        if unassigned:
            if tier == 'High':
                # Suggest Advanced/AI topics
                advanced = next((m for m in unassigned if "AI" in m['title'] or "Future" in m['title']), None)
                if advanced:
                    recs.append({"module": advanced, "reason": "Advanced Challenge (High LCI)", "type": "growth"})
            
            elif tier == 'Low':
                # Suggest Foundations
                recs.append({"module": unassigned[0], "reason": "Recommended Foundation", "type": "growth"})
            
            else:
                # Medium
                recs.append({"module": unassigned[0], "reason": "Suggested Next Step", "type": "growth"})
                
        return recs[:3]

    # ... (Keep generate_quiz and grade_quiz) ...
    def generate_quiz(self, module_title, module_summary, distribution=None):
        if not hasattr(self, 'fast_brain'):
             genai.configure(api_key=self.google_key)
             self.fast_brain = genai.GenerativeModel('gemini-flash-latest')
        
        if not distribution: distribution = {"Easy": 1, "Medium": 1, "Hard": 1}
        
        prompt = f"""
        Create a 3-question quiz for "{module_title}".
        Context: {module_summary}
        Requirements: {distribution.get('Easy')} Easy, {distribution.get('Medium')} Medium, {distribution.get('Hard')} Hard.
        Return JSON: [{{ "q": "Question?", "options": ["A)", "B)"], "correct": "A", "difficulty": "Easy" }}]
        """
        try:
            res = self.fast_brain.generate_content(prompt).text
            return json.loads(res.replace("```json", "").replace("```", "").strip())
        except: return []

    def grade_quiz(self, module_title, user_answers, quiz_data):
        score = 0
        feedback = []
        for i, q in enumerate(quiz_data):
            user_ans = user_answers.get(i)
            if user_ans and str(user_ans).startswith(q['correct']):
                score += 1
                feedback.append(f"Q{i+1}: ✅ Correct")
            else:
                feedback.append(f"Q{i+1}: ❌ Incorrect")
        return {"score_percent": (score/len(quiz_data))*100, "feedback": "\n".join(feedback)}