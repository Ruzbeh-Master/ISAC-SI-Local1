import streamlit as st
import pandas as pd
import plotly.express as px
import time
import io
from gtts import gTTS
from PIL import Image

# Custom Modules
from modules.isac_agent import ISACDualAgent
from modules.db_handler import (
    init_db, save_syllabus_document, get_all_documents, 
    delete_document, save_parsed_chapters, assign_module_to_student,
    update_student_profile, save_db, 
    save_chat_session, load_chat_session, get_student_dataframe
)
from modules.ai_ingest import parse_pdf_content, ai_structure_syllabus
from modules.lci_engine import LCIEngine

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(page_title="ISAC SI Core", layout="wide", page_icon="🧠")

# ISAC Navy Theme (Matches React App)
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0a192f; color: #8892b0; }
    
    /* Text Colors */
    h1, h2, h3, h4 { color: #ccd6f6 !important; }
    p, label, .stMarkdown, .stText, .stCaption { color: #8892b0 !important; }
    
    /* Cards & Containers */
    div.stContainer, div[data-testid="stMetric"], div.stDataFrame, div[data-testid="stForm"] {
        background-color: #112240; 
        border: 1px solid #233554; 
        border-radius: 8px; 
        padding: 15px;
    }
    
    /* Metrics */
    div[data-testid="metric-value"] { color: #64ffda !important; }
    div[data-testid="metric-label"] { color: #a8b2d1 !important; }
    
    /* Buttons */
    div.stButton > button {
        background-color: #64ffda;
        color: #0a192f;
        font-weight: bold;
        border: none;
        border-radius: 4px;
    }
    div.stButton > button:hover { opacity: 0.8; }
    
    /* Chat Bubbles */
    .user-msg { background-color: #64ffda; color: #0a192f; padding: 10px; border-radius: 10px 10px 0 10px; margin-bottom: 5px; text-align: right; }
    .bot-msg { background-color: #112240; color: #ccd6f6; border: 1px solid #233554; padding: 10px; border-radius: 10px 10px 10px 0; margin-bottom: 5px; }
    .layer-badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; border: 1px solid; margin-top: 5px; display: inline-block; }
    
    /* Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        background-color: #112240;
        color: #ccd6f6;
        border: 1px solid #233554;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
if 'db' not in st.session_state: st.session_state.db = init_db()
if 'user' not in st.session_state: st.session_state.user = None
if 'chat_sessions' not in st.session_state: st.session_state.chat_sessions = [{"id": "1", "title": "New Session", "msgs": []}]

agent = ISACDualAgent()

# --- 3. HELPER COMPONENTS ---

def render_login():
    """Login Screen"""
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><h1 style='text-align: center; font-size: 60px;'>ISAC</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Integrated System Assistance Core</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="student@mrdinstitute.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Sign In"):
                role = "Student"
                if "tutor" in email.lower(): role = "Tutor"
                if "director" in email.lower(): role = "Director"
                
                # Auth Logic
                user_data = next((s for s in st.session_state.db['students'] if s.get('email', '').lower() == email.lower() or s['name'].lower() in email.lower()), st.session_state.db['students'][0])
                
                st.session_state.user = {"email": email, "role": role, "data": user_data}
                # Load History
                st.session_state.chat_sessions = load_chat_session(email)
                st.rerun()

def render_syllabus_manager():
    """Syllabus Upload & Management"""
    st.markdown("### 🗄️ Syllabus Database")
    
    with st.expander("📤 Upload New Document", expanded=True):
        uploaded_file = st.file_uploader("Select PDF or Word Doc", type=['pdf', 'docx'])
        
        if uploaded_file and st.button("Save to Database"):
            with st.spinner("Processing & Encrypting..."):
                # 1. Save File Metadata
                doc = save_syllabus_document(uploaded_file, uploaded_by=st.session_state.user['role'])
                st.success(f"Saved: {doc['fileName']}")
                
                # 2. AI Ingest
                text = parse_pdf_content(uploaded_file)
                if text:
                    chapters = ai_structure_syllabus(text)
                    count = save_parsed_chapters(chapters)
                    st.toast(f"AI extracted {count} chapters")
                st.rerun()

    # List Documents
    docs = get_all_documents()
    if docs:
        st.markdown(f"**Stored Documents ({len(docs)})**")
        for doc in docs:
            c1, c2, c3, c4 = st.columns([0.5, 4, 2, 1])
            with c1: st.markdown("📄" if doc['fileType'] == 'pdf' else "📝")
            with c2: 
                st.markdown(f"**{doc['title']}**")
                st.caption(f"Uploaded by {doc['uploadedBy']}")
            with c3: st.text(doc['size'])
            with c4:
                if st.button("🗑️", key=doc['id']):
                    delete_document(doc['id'])
                    st.rerun()
    else:
        st.info("No documents found.")

def render_inbox():
    """Notification Inbox"""
    st.title("📬 Notification Center")
    student = st.session_state.user['data']
    msgs = student.get('notifications', [])
    
    if not msgs: st.info("No new notifications.")
        
    for m in msgs:
        with st.container():
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{m['title']}**")
                st.caption(m['msg'])
            with c2:
                st.text(m.get('date', 'Today'))
                if st.button("Mark Read", key=f"read_{m['id']}"):
                    st.toast("Marked as read")

def render_profile():
    """Profile, Skills & Editing"""
    st.title("My Profile")
    user = st.session_state.user['data']
    
    t1, t2 = st.tabs(["📊 Performance", "⚙️ Account Settings"])
    
    with t1:
        c1, c2 = st.columns([1, 2])
        with c1:
            lci = user.get('lci', {})
            score = lci.get('overallScore', 0.5) if isinstance(lci, dict) else 0.5
            tier = lci.get('tier', 'Medium') if isinstance(lci, dict) else 'Medium'
            
            st.metric("LCI Score", f"{score:.2f}")
            st.info(f"Current Tier: **{tier}**")
            
            categories = ['Accuracy', 'Time', 'Engagement', 'Consistency', 'Confidence']
            fig = px.line_polar(r=[score]*5, theta=categories, line_close=True)
            fig.update_traces(fill='toself', line_color='#64ffda')
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': '#8892b0'})
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("Concept Mastery Graph")
            my_skills = user.get('skills', {})
            if my_skills:
                df_skill = pd.DataFrame(list(my_skills.items()), columns=['Concept', 'Mastery'])
                fig_skill = px.bar(df_skill, x='Concept', y='Mastery', color='Mastery', range_y=[0, 100])
                fig_skill.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': '#8892b0'})
                st.plotly_chart(fig_skill, use_container_width=True)
            else:
                st.info("Complete quizzes to unlock your Knowledge Graph.")

    with t2:
        with st.form("edit_profile"):
            new_name = st.text_input("Full Name", value=user.get('name', ''))
            new_bio = st.text_area("Bio", value=user.get('bio', ''))
            new_pass = st.text_input("New Password", type="password", help="Leave empty to keep current")
            
            if st.form_submit_button("Save Changes"):
                update_student_profile(user.get('email', user['name']), new_name, new_bio, new_pass)
                st.session_state.user['data']['name'] = new_name
                st.session_state.user['data']['bio'] = new_bio
                st.success("Profile Updated!")
                time.sleep(1)
                st.rerun()

# --- 4. DASHBOARD PAGES ---

def render_director():
    """Director Dashboard"""
    st.title("🕵️‍♂️ Director Dashboard")
    
    k1, k2, k3, k4 = st.columns(4)
    students = st.session_state.db['students']
    avg_lci = sum([s.get('lci', {}).get('overallScore', 0.5) if isinstance(s.get('lci'), dict) else 0.5 for s in students]) / len(students)
    
    at_risk = 0
    for s in students:
        risk, _ = agent.predict_student_risk(s)
        if "CRITICAL" in risk or "HIGH" in risk: at_risk += 1
    
    k1.metric("Student Body", len(students))
    k2.metric("Inst. LCI Score", f"{avg_lci:.2f}")
    k3.metric("At-Risk Students", at_risk, delta="-2" if at_risk < 2 else "0", delta_color="inverse")
    k4.metric("System Status", "Online")

    t1, t2, t3 = st.tabs(["📊 Analytics", "📋 Reports", "🗄️ Repository"])
    
    with t1:
        st.subheader("Intervention Required")
        for s in students:
            risk, reason = agent.predict_student_risk(s)
            if risk != "🟢 STABLE":
                with st.expander(f"{risk} : {s['name']}"):
                    st.write(f"**Reason:** {reason}")
                    if st.button("Generate Intervention Plan", key=f"int_{s['name']}"):
                        st.info(f"ISAC suggests: Schedule 1:1 mentorship session focusing on {reason}")

    with t2:
        st.subheader("Administrative Reports")
        df_students = get_student_dataframe()
        csv = df_students.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download Student Risk Report (CSV)",
            data=csv,
            file_name="isac_student_risk_report.csv",
            mime="text/csv",
        )
        st.dataframe(df_students, hide_index=True)

    with t3:
        render_syllabus_manager()

def render_tutor():
    """Tutor Dashboard"""
    st.title("👩‍🏫 Tutor Dashboard")
    t1, t2 = st.tabs(["🎓 Student Management", "📚 Curriculum Manager"])
    
    with t1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### Manage Student")
            students = st.session_state.db['students']
            selected_student_name = st.selectbox("Select Student", [s['name'] for s in students])
            student = next(s for s in students if s['name'] == selected_student_name)
            
            lci = student.get('lci', {})
            score = lci.get('overallScore', 0.5) if isinstance(lci, dict) else 0.5
            tier = lci.get('tier', 'Medium') if isinstance(lci, dict) else 'Medium'
            
            st.metric("LCI Score", f"{score:.2f}")
            st.info(f"Tier: {tier}")
            
            categories = ['Accuracy', 'Time', 'Engagement', 'Consistency', 'Confidence']
            fig = px.line_polar(r=[score]*5, theta=categories, line_close=True)
            fig.update_traces(fill='toself', line_color='#64ffda')
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': '#8892b0'})
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("### Assign Modules")
            chapters = st.session_state.db.get('syllabus_chapters', [])
            if chapters:
                for chap in chapters:
                    with st.expander(f"{chap['title']} ({chap['difficulty']})"):
                        st.write(chap['summary'])
                        if st.button(f"Assign to {student['name']}", key=chap['id']):
                            assign_module_to_student(student['name'], chap['id'])
                            st.toast("Assignment Sent!")
            else:
                st.warning("No chapters available.")
    with t2:
        render_syllabus_manager()

def render_student():
    """Student Dashboard: Learning Hub, Study Planner & Tools"""
    student = st.session_state.user['data']
    st.title(f"Welcome, {student['name']}")
    
    tab1, tab2 = st.tabs(["📚 Learning Hub", "📅 AI Study Planner"])
    
    # --- TAB 1: LEARNING HUB ---
    with tab1:
        col_nav, col_main = st.columns([1, 2])
        
        with col_nav:
            st.subheader("Assigned Modules")
            my_ids = student.get('assignments', [])
            all_chapters = st.session_state.db.get('syllabus_chapters', [])
            my_modules = [m for m in all_chapters if m['id'] in my_ids]
            
            recs = agent.get_recommendations(student, all_chapters)
            if recs:
                st.markdown("#### ✨ AI Suggested Focus")
                for rec in recs:
                    st.info(f"**{rec['module']['title']}**\n\nReason: {rec['reason']}")

            selected_mod_title = st.radio("Select Module", [m['title'] for m in my_modules]) if my_modules else None

        with col_main:
            if selected_mod_title:
                module = next(m for m in my_modules if m['title'] == selected_mod_title)
                st.markdown(f"## {module['title']}")
                st.caption(f"Difficulty: {module['difficulty']}")

                # --- SMART TOOLS TOOLBAR ---
                st.markdown("### 🛠️ Smart Tools")
                c1, c2, c3 = st.columns(3)
                
                if 'adapted_text' not in st.session_state: st.session_state.adapted_text = None
                if 'active_mod_id' not in st.session_state or st.session_state.active_mod_id != module['id']:
                    st.session_state.adapted_text = None 
                    st.session_state.active_mod_id = module['id']

                with c1:
                    if st.button("💡 Simplify (ELI5)"):
                        with st.spinner("ISAC is simplifying concepts..."):
                            raw = module.get('theory', module['summary'])
                            st.session_state.adapted_text = agent.adapt_content(raw, "Simplify")
                
                with c2:
                    if st.button("🔬 Deep Dive"):
                        with st.spinner("Expanding technical depth..."):
                            raw = module.get('theory', module['summary'])
                            st.session_state.adapted_text = agent.adapt_content(raw, "Deep Dive")
                            
                with c3:
                    if st.button("🚗 Analogy Mode"):
                        with st.spinner("Generating analogies..."):
                            raw = module.get('theory', module['summary'])
                            st.session_state.adapted_text = agent.adapt_content(raw, "Analogy")

                st.divider()
                
                # --- CONTENT & AUDIO ---
                display_text = st.session_state.adapted_text if st.session_state.adapted_text else module.get('theory', module['summary'])
                
                if st.checkbox("🔊 Listen to Content"):
                    try:
                        tts = gTTS(text=display_text[:1000], lang='en') 
                        audio_fp = io.BytesIO()
                        tts.write_to_fp(audio_fp)
                        st.audio(audio_fp, format='audio/mp3')
                    except: st.warning("Audio unavailable.")

                with st.container():
                    if st.session_state.adapted_text:
                        st.info(f"**ISAC Adapted Content:**\n\n{display_text}")
                        if st.button("Revert to Original"):
                            st.session_state.adapted_text = None
                            st.rerun()
                    else:
                        st.markdown(f"### Core Theory\n{display_text}")

                # --- QUIZ LAUNCHER ---
                st.divider()
                if st.button("Start Adaptive Quiz"):
                    lci_data = student.get('lci', {})
                    acc = lci_data.get('accuracy', 0.5) if isinstance(lci_data, dict) else 0.5
                    conf = lci_data.get('confidence', 0.5) if isinstance(lci_data, dict) else 0.5
                    
                    dist = LCIEngine().calculate_quiz_distribution(acc, conf)
                    quiz = agent.generate_quiz(module['title'], module['summary'], dist)
                    
                    st.session_state.quiz_active = True
                    st.session_state.active_module = module
                    st.session_state.current_quiz = quiz
                    st.session_state.quiz_dist = dist
                    st.rerun()
            else:
                st.info("Select a module to begin.")

    # --- TAB 2: STUDY PLANNER ---
    with tab2:
        st.subheader("Optimization Layer: Study Schedule")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Pending Modules", len(student.get('assignments', [])))
            if st.button("⚡ Generate New Schedule"):
                with st.spinner("Optimizing timeline..."):
                    all_chapters = st.session_state.db.get('syllabus_chapters', [])
                    plan = agent.generate_study_plan(student, all_chapters)
                    st.session_state.current_plan = plan
        with c2:
            if 'current_plan' in st.session_state:
                st.markdown(st.session_state.current_plan)
                st.download_button("📥 Download Plan", st.session_state.current_plan, "my_study_plan.md")

# --- 5. CHATBOT ---

def render_chat():
    """Neural Chat Interface"""
    st.title("🤖 ISAC Neural Chat")
    
    with st.sidebar:
        st.markdown("---")
        st.caption("History")
        if st.button("+ New Chat", use_container_width=True):
            new_id = str(len(st.session_state.chat_sessions) + 1)
            st.session_state.chat_sessions.insert(0, {"id": new_id, "title": "New Session", "msgs": []})
            st.rerun()
            
        for idx, s in enumerate(st.session_state.chat_sessions):
            if idx < 5:
                if st.button(f"💬 {s['title'][:15]}...", key=f"sess_{idx}", use_container_width=True):
                    active = st.session_state.chat_sessions.pop(idx)
                    st.session_state.chat_sessions.insert(0, active)
                    st.rerun()

    session = st.session_state.chat_sessions[0]
    
    for msg in session['msgs']:
        if msg['role'] == 'user':
            st.markdown(f"<div class='user-msg'>{msg['text']}</div>", unsafe_allow_html=True)
            if 'image' in msg: st.image(msg['image'], width=200)
        else:
            color = "#64ffda"
            if msg.get('layer') == 'Cognitive': color = "#3b82f6"
            elif msg.get('layer') == 'Assessment': color = "#ea580c"
            elif msg.get('layer') == 'Engagement': color = "#9333ea"
            elif msg.get('layer') == 'Optimization': color = "#475569"
            
            st.markdown(f"""
            <div class='bot-msg'>{msg['text']}<br>
            <span class='layer-badge' style='color:{color}; border-color:{color}'>{msg.get('layer', 'Operational')}</span>
            </div>""", unsafe_allow_html=True)

    with st.form("chat_input", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        text_in = c1.text_input("Message...", label_visibility="collapsed")
        uploaded_img = c2.file_uploader("📷", type=['png', 'jpg'], label_visibility="collapsed")
        
        if st.form_submit_button("Send") and (text_in or uploaded_img):
            msg_data = {"role": "user", "text": text_in}
            pil_image = None
            if uploaded_img:
                pil_image = Image.open(uploaded_img)
                msg_data["image"] = pil_image
                msg_data["text"] += " [Image]"
            
            session['msgs'].append(msg_data)
            if len(session['msgs']) == 1: session['title'] = text_in[:20] if text_in else "Image Query"
            
            with st.spinner("Processing..."):
                res = agent.process_query(text_in, st.session_state.user['data']['name'], "Medium", attachment=pil_image)
                session['msgs'].append({"role": "bot", "text": res['response'], "layer": res['active_layer']})
            
            save_chat_session(st.session_state.user['email'], st.session_state.chat_sessions)
            st.rerun()

# --- 6. MAIN ROUTER ---

if not st.session_state.user:
    render_login()
else:
    with st.sidebar:
        st.title("ISAC CORE")
        st.caption(f"Role: {st.session_state.user['role']}")
        options = ["Dashboard", "ChatBot", "Inbox", "Profile", "Log Out"]
        choice = st.radio("Navigate", options)
        if choice == "Log Out":
            st.session_state.user = None
            st.rerun()

    if choice == "ChatBot": render_chat()
    elif choice == "Inbox": render_inbox()
    elif choice == "Profile": render_profile()
    elif choice == "Dashboard":
        role = st.session_state.user['role']
        if role == "Student":
            if st.session_state.get('quiz_active'):
                # QUIZ INTERFACE
                st.title(f"Quiz: {st.session_state.active_module['title']}")
                q_dist = st.session_state.get('quiz_dist', {})
                st.caption(f"Adaptive Mode: {q_dist.get('Hard',0)} Hard, {q_dist.get('Medium',0)} Med")
                
                with st.form("quiz_form"):
                    ans = {}
                    for i, q in enumerate(st.session_state.current_quiz):
                        st.markdown(f"**Q{i+1}: {q['q']}**")
                        ans[i] = st.radio("Answer:", q['options'], key=i)
                        st.divider()
                    if st.form_submit_button("Submit"):
                        res = agent.grade_quiz("", ans, st.session_state.current_quiz)
                        st.success(f"Score: {res['score_percent']:.0f}%")
                        if st.button("Finish"): 
                            mod_tags = st.session_state.active_module.get('tags', [])
                            curr_skills = st.session_state.user['data'].get('skills', {})
                            new_skills = agent.calculate_skill_mastery(mod_tags, res['score_percent'], curr_skills)
                            st.session_state.user['data']['skills'] = new_skills
                            save_db(st.session_state.db)
                            st.session_state.quiz_active = False
                            st.rerun()
            else:
                render_student()
        elif role == "Director": render_director()
        elif role == "Tutor": render_tutor()