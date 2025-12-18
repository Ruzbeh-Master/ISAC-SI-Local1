import streamlit as st
import pandas as pd
import os
import time

# --- SETUP ---
st.set_page_config(page_title="ISAC SI Core", layout="wide", page_icon="🧠")

try:
    from modules.lci_engine import LCIEngine
    from modules.isac_agent import ISACReportingAgent
    from modules.db_handler import init_db, log_interaction
    import google.generativeai as genai
    import openai
except ImportError as e:
    st.error(f"Missing Module: {e}. Check your 'modules' folder.")
    st.stop()

# --- CSS & THEME ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #000000; }
    h1, h2, h3 { color: #000000 !important; }
    div[data-testid="metric-container"] {
        background-color: #f6f8fa; border: 1px solid #d0d7de; color: black;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 10px; border-radius: 6px;
    }
    .stChatMessage { background-color: #ffffff; border: 1px solid #e1e4e8; }
    div.stButton > button { background-color: #2da44e; color: white; border: none; }
</style>
""", unsafe_allow_html=True)

# --- INIT ---
if 'db_data' not in st.session_state:
    st.session_state.db_data = init_db()
    st.session_state.data = st.session_state.db_data['students']

lci_engine = LCIEngine()
agent = ISACReportingAgent()

# API Keys
google_key = st.secrets.get("GOOGLE_API_KEY")
if google_key: genai.configure(api_key=google_key)
openai_key = st.secrets.get("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=openai_key) if openai_key else None

# --- SIDEBAR ---
with st.sidebar:
    st.title("ISAC CORE")
    mode = st.radio("Menu", ["Dashboard", "Neural Router", "Student Mode", "Reports"])
    st.divider()
    st.caption(f"Gemini: {'🟢' if google_key else '🔴'}")
    st.caption(f"GPT-4o: {'🟢' if openai_client else '🔴'}")

# --- PAGES ---
if mode == "Dashboard":
    st.title("🖥️ Command Center")
    df = pd.DataFrame(st.session_state.data)
    risk_count = len([s for s in st.session_state.data if s.get('lci', 0) < 0.45])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Cohort", len(df))
    c2.metric("Avg LCI", f"{df.get('lci', pd.Series([0])).mean():.2f}")
    c3.metric("Critical Risks", risk_count, delta_color="inverse")
    
    t1, t2 = st.tabs(["🚨 Risk Board", "📚 Ingestion"])
    
    with t1:
        for s in st.session_state.data:
            risk, reasons = agent.predict_risk(s)
            if risk != "🟢 STABLE":
                with st.expander(f"{risk}: {s['name']}"):
                    st.write(reasons)
                    if st.button("Generate Plan", key=s['name']):
                        with st.spinner("Thinking..."):
                            st.info(agent.generate_intervention(s['name'], reasons))
                            
    with t2:
        up_file = st.file_uploader("Upload PDF", type="pdf")
        if up_file and st.button("Ingest"):
            from modules.ai_ingest import parse_textbook, save_syllabus
            syl, msg = parse_textbook(up_file)
            if syl: save_syllabus(syl); st.success("Done!")
            else: st.error(msg)

elif mode == "Neural Router":
    st.title("🔀 Neural Router")
    q = st.text_input("Simulate Query:", "I'm stressed and I don't get physics.")
    if st.button("Route"):
        try:
            # 1. Router
            route = genai.GenerativeModel('gemini-flash-latest').generate_content(f"Classify '{q}' as FACTUAL or EMOTIONAL (one word).").text.strip()
            st.info(f"Route: {route}")
            
            # 2. Solver
            if "EMOTIONAL" in route and openai_client:
                ans = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":q}]).choices[0].message.content
                src = "GPT-4o"
            else:
                ans = genai.GenerativeModel('gemini-flash-latest').generate_content(q).text
                src = "Gemini"
            
            st.success(f"Response ({src}):")
            st.write(ans)
        except Exception as e:
            st.error(f"Error: {e}")

elif mode == "Student Mode":
    st.title("🎓 Student Learning")
    name = st.selectbox("Identity", [s['name'] for s in st.session_state.data])
    student = next(s for s in st.session_state.data if s['name'] == name)
    
    if "msgs" not in st.session_state: st.session_state.msgs = []
    for m in st.session_state.msgs: st.chat_message(m['role']).write(m['content'])
    
    if prompt := st.chat_input():
        st.session_state.msgs.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # AI Response
        model = genai.GenerativeModel('gemini-flash-latest')
        res = model.generate_content(f"Tutor for {student['tier']} student. Q: {prompt}").text
        st.chat_message("assistant").write(res)
        st.session_state.msgs.append({"role": "assistant", "content": res})
        
        # Background Scoring
        new_met = agent.score_interaction(prompt, res)
        new_lci = lci_engine.calculate_lci(new_met)
        new_tier = lci_engine.get_student_tier(new_lci)
        
        # DB Update
        log_interaction(name, {'new_metrics': new_met, 'new_lci': new_lci, 'new_tier': new_tier})
        st.toast(f"LCI Updated: {new_lci:.2f}")

elif mode == "Reports":
    st.title("📑 Reporting")
    if st.button("Generate Cohort Report"):
        with st.spinner("Writing..."):
            st.markdown(agent.generate_program_performance_report(st.session_state.data))