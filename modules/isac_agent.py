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
        # ---------------------------------------------------------
        # 👇 PASTE YOUR NEW API KEY INSIDE THE QUOTES BELOW 👇
        # ---------------------------------------------------------
        self.google_key = "AIzaSyB7CXelkxypu2x5-gjfKAbebI_0FhlczaA" 
        
        if self.google_key:
            try:
                genai.configure(api_key=self.google_key)
                self.fast_brain = genai.GenerativeModel('gemini-flash-latest') 
            except Exception as e:
                print(f"ISAC Init Error: {e}")
                
    # --- NEW: Adaptive Content Engine ---
    def adapt_content(self, raw_text, mode="Simplify"):
        """
        Rewrites educational content based on the requested mode.
        Modes: 'Simplify' (ELI5), 'Deep Dive' (Academic), 'Analogy' (Real-world examples).
        """
        prompt = f"""
        Role: Expert Teacher.
        Task: Rewrite the following engineering concept.
        Mode: {mode}
        
        Guidelines:
        - If 'Simplify': Use simple language, short sentences, and explain like I'm 15.
        - If 'Deep Dive': Add mathematical context, advanced terminology, and research references.
        - If 'Analogy': Explain the concept using a real-world analogy (e.g., cars, water, sports).
        
        Original Text:
        "{raw_text}"
        
        Output: The rewritten text ONLY.
        """
        try:
            return self.fast_brain.generate_content(prompt).text
        except:
            return "Neural adaptation failed. Showing original text."            

    def determine_layer(self, query):
        q = query.lower()
        if any(x in q for x in ['quiz', 'test', 'score', 'grade']): return "Assessment"
        if any(x in q for x in ['why', 'how', 'explain', 'concept']): return "Cognitive"
        if any(x in q for x in ['plan', 'schedule', 'next', 'track']): return "Optimization"
        if any(x in q for x in ['help', 'hello', 'hi', 'thanks']): return "Engagement"
        return "Operational"

    def process_query(self, user_query, student_name, student_tier, attachment=None):
        if not self.google_key or "PASTE_YOUR" in self.google_key:
            return {"response": "⚠️ API Key Missing. Please update isac_agent.py with your Google AI Key.", "active_layer": "Operational"}

        # 1. Determine Layer
        active_layer = self.determine_layer(user_query)

        # 2. Check Syllabus (Text Only)
        syllabus_context = search_syllabus(user_query)
        context_msg = f"CONTEXT: {syllabus_context}" if syllabus_context else ""

        # 3. Prepare Input for Gemini
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
            inputs.append(attachment) 

        try:
            response = self.fast_brain.generate_content(inputs)
            response_text = response.text
        except Exception as e:
            response_text = f"I encountered a neural processing error: {str(e)}"

        return {
            "response": response_text,
            "active_layer": active_layer
        }

    def generate_quiz(self, module_title, module_summary, distribution=None):
        if not hasattr(self, 'fast_brain'): return []
        
        if not distribution: distribution = {"Easy": 1, "Medium": 1, "Hard": 1}
        
        prompt = f"""
        Create a 3-question quiz for "{module_title}".
        Context: {module_summary}
        Requirements: {distribution.get('Easy', 0)} Easy, {distribution.get('Medium', 0)} Medium, {distribution.get('Hard', 0)} Hard.
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

    def calculate_skill_mastery(self, module_tags, quiz_score, current_skills):
        updated_skills = current_skills.copy()
        factor = max(0.1, (quiz_score - 50) / 50) 
        
        if quiz_score >= 60: 
            for tag in module_tags:
                current_val = updated_skills.get(tag, 0)
                improvement = (100 - current_val) * 0.1 * factor
                updated_skills[tag] = min(100, current_val + improvement)
        return updated_skills

    def predict_student_risk(self, student_profile):
        lci = student_profile.get('lci', {})
        if not isinstance(lci, dict): return "Unknown", "Insufficient Data"
        
        score = lci.get('overallScore', 0.5)
        
        if score < 0.35: return "🔴 CRITICAL", "Academic failure imminent."
        elif score < 0.5: return "🟠 HIGH", "Disengagement detected."
        elif score < 0.7: return "🟡 MODERATE", "Erratic learning patterns."
        else: return "🟢 STABLE", "Optimal parameters."

    def get_recommendations(self, student_data, all_modules):
        recs = []
        lci_data = student_data.get('lci', {})
        tier = lci_data.get('tier', 'Medium') if isinstance(lci_data, dict) else 'Medium'
        
        unassigned = [m for m in all_modules if m['id'] not in student_data.get('assignments', [])]
        
        if unassigned:
            if tier == 'High':
                advanced = next((m for m in unassigned if "AI" in m['title']), None)
                if advanced: recs.append({"module": advanced, "reason": "Advanced Challenge (High LCI)"})
            else:
                recs.append({"module": unassigned[0], "reason": "Recommended Next Step"})
        return recs[:3]

    def generate_study_plan(self, student_data, all_modules):
        assigned_ids = student_data.get('assignments', [])
        todo_modules = [m['title'] for m in all_modules if m['id'] in assigned_ids]
        
        if not todo_modules: return "No pending assignments."

        tier = student_data.get('lci', {}).get('tier', 'Medium')
        
        prompt = f"""
        Role: Academic Counselor. Student Tier: {tier}. Pending: {', '.join(todo_modules)}.
        Task: Create a 3-Day Study Schedule Markdown Table.
        """
        try:
            return self.fast_brain.generate_content(prompt).text
        except: return "Could not generate plan."