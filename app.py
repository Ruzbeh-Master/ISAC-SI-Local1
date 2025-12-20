import streamlit as st
import pandas as pd
import plotly.express as px
import time
from PIL import Image
from modules.isac_agent import ISACDualAgent
from modules.db_handler import (
    init_db, save_syllabus_document, get_all_documents, 
    delete_document, save_parsed_chapters, assign_module_to_student,
    update_student_profile
)
from modules.ai_ingest import parse_pdf_content, ai_structure_syllabus
from modules.lci_engine import LCIEngine

# --- CONFIG & THEME ---
st.set_page_config(page_title="ISAC SI Core", layout="wide", page_icon="🧠")

# Force ISAC Navy Theme
st.markdown("""
<style>
    .stApp { background-color: #0a192f; color: #8892b0; }
    h1, h2, h3, h4 { color: #ccd6f6 !important; }
    p, label, .stMarkdown, .stText, .stCaption { color: #8892b0 !important; }
    
    div.stContainer, div[data-testid="stMetric"], div.stDataFrame, div[data-testid="stForm"] {
        background-color: #112240; border: 1px solid #233554; border-radius: 8px; padding: 15px;
    }
    
    div[data-testid="metric-value"] { color: #64ffda !important; }
    div.stButton > button { background-color: #64ffda; color: #0a192f; font-weight: bold; border: none; }
    div.stButton > button:hover { opacity: 0.8; }
    
    .user-msg { background-color: #64ffda; color: #0a192f; padding: 10px; border-radius: 10px 10px 0 10px; margin-bottom: 5px; text-align: right; }
    .bot-msg { background-color: #112240; color: #ccd6f6; border: 1px solid #233554; padding: 10px; border-radius: 10px 10px 10px 0; margin-bottom: 5px; }
    .layer-badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; border: 1px solid; margin-top: 5px; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# --- INIT STATE ---
if 'db' not in st.session_state: st.session_state.db = init_db()
if 'user' not in st.session_state: st.session_state.user = None
if 'chat_sessions' not in st.session_state: st.session_state.chat_sessions = [{"id": "1", "title": "New Session", "msgs": []}]

agent = ISACDualAgent()

# --- COMPONENT: LOGIN ---
def render_login():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><h1 style='text-align: center; font-size: 60px;'>ISAC</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Integrated System Assistance Core</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="student@mrdinstitute.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Sign In"):
                role = "Student"
                if "tutor" in email.lower(): role = "Tutor"
                if "director" in email.lower(): role = "Director"
                
                # Mock Login
                user_data = next((s for s in st.session_state.db['students'] if s['name'].lower() in email.lower()), st.session_state.db['students'][0])
                
                st.session_state.user = {
                    "email": email,
                    "role": role,
                    "data": user_data
                }
                st.rerun()

# --- COMPONENT: SYLLABUS MANAGER ---
def render_syllabus_manager():
    st.markdown("### 🗄️ Syllabus Database")
    with st.expander("📤 Upload New Document", expanded=True):
        uploaded_file = st.file_uploader("Select PDF or Word Doc", type=['pdf', 'docx'])
        if uploaded_file and st.button("Save to Database"):
            with st.spinner("Processing..."):
                doc = save_syllabus_document(uploaded_file, uploaded_by=st.session_state.user['role'])
                st.success(f"Saved: {doc['fileName']}")
                text = parse_pdf_content(uploaded_file)
                if text:
                    chapters = ai_structure_syllabus(text)
                    count = save_parsed_chapters(chapters)
                    st.toast(f"AI extracted {count} chapters")
                st.rerun()

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

# --- COMPONENT: PROFILE PAGE (This was missing!) ---
def render_profile():
    st.title("My Profile")
    user = st.session_state.user['data']
    
    t1, t2 = st.tabs(["📊 Performance", "⚙️ Account Settings"])
    
    with t1:
        c1, c2 = st.columns([1, 2])
        with c1:
            # Safe LCI Access
            lci = user.get('lci', {})
            score = lci.get('overallScore', 0.5) if isinstance(lci, dict) else (lci if isinstance(lci, float) else 0.5)
            tier = lci.get('tier', user.get('tier', 'Medium')) if isinstance(lci, dict) else user.get('tier', 'Medium')
            
            st.metric("LCI Score", f"{score:.2f}")
            st.info(f"Current Tier: **{tier}**")
            
            categories = ['Accuracy', 'Time', 'Engagement', 'Consistency', 'Confidence']
            r_values = [score] * 5 
            fig = px.line_polar(r=r_values, theta=categories, line_close=True)
            fig.update_traces(fill='toself', line_color='#64ffda')
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': '#8892b0'})
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("Quiz Progress")
            progress = user.get('progress', {})
            if progress:
                df_prog = pd.DataFrame(list(progress.items()), columns=['Module', 'Score'])
                fig_bar = px.bar(df_prog, x='Module', y='Score', color='Score', color_continuous_scale=["#ef4444", "#64ffda"])
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': '#8892b0'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No quiz data recorded yet.")

    with t2:
        with st.form("edit_profile"):
            new_name = st.text_input("Full Name", value=user.get('name', ''))
            new_bio = st.text_area("Bio", value=user.get('bio', ''))
            new_pass = st.text_input("New Password", type="password", help="Leave empty to keep current")
            
            if st.form_submit_button("Save Changes"):
                update_student_profile(user.get('email', user['name']), new_name, new_bio, new_pass)
                # Live Update Session
                st.session_state.user['data']['name'] = new_name
                st.session_state.user['data']['bio'] = new_bio
                st.success("Profile Updated!")
                time.sleep(1)
                st.rerun()

# --- COMPONENT: INBOX ---
def render_inbox():
    st.title("📬 Notification Center")
    student = st.session_state.user['data']
    msgs = student.get('notifications', [])
    
    if not msgs:
        st.info("No new notifications.")
        
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

# --- COMPONENT: STUDENT DASHBOARD ---
def render_student():
    student = st.session_state.user['data']
    st.title(f"Welcome, {student['name']}")
    
    col_nav, col_main = st.columns([1, 2])
    
    with col_nav:
        st.subheader("Assigned Modules")
        my_ids = student.get('assignments', [])
        all_chapters = st.session_state.db.get('syllabus_chapters', [])
        my_modules = [m for m in all_chapters if m['id'] in my_ids]
        
        # AI Recommendations
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
            
            with st.container():
                st.markdown("### 🧠 AI Summary")
                st.info(module['summary'])
            
            with st.expander("📖 Read Module Theory", expanded=True):
                st.markdown(module.get('theory', "No text content available."))

            if st.button("Start Adaptive Quiz"):
                lci = student.get('lci', {})
                acc = lci.get('accuracy', 0.5) if isinstance(lci, dict) else 0.5
                conf = lci.get('confidence', 0.5) if isinstance(lci, dict) else 0.5
                
                dist = LCIEngine().calculate_quiz_distribution(acc, conf)
                quiz = agent.generate_quiz(module['title'], module['summary'], dist)
                
                st.session_state.quiz_active = True
                st.session_state.active_module = module
                st.session_state.current_quiz = quiz
                st.session_state.quiz_dist = dist
                st.rerun()
        else:
            st.info("Select a module to begin.")

# --- COMPONENT: CHATBOT ---
def render_chat():
    st.title("🤖 ISAC Neural Chat")
    session = st.session_state.chat_sessions[0]
    
    for msg in session['msgs']:
        if msg['role'] == 'user':
            st.markdown(f"<div class='user-msg'>{msg['text']}</div>", unsafe_allow_html=True)
            if 'image' in msg: st.image(msg['image'], width=200)
        else:
            color = "#64ffda"
            if msg.get('layer') == 'Cognitive': color = "#3b82f6"
            elif msg.get('layer') == 'Assessment': color = "#ea580c"
            
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
            
            with st.spinner("Thinking..."):
                res = agent.process_query(text_in, st.session_state.user['data']['name'], "Medium", attachment=pil_image)
                session['msgs'].append({"role": "bot", "text": res['response'], "layer": res['active_layer']})
            st.rerun()

# --- DASHBOARD ROLES ---
def render_director():
    st.title("Director Dashboard")
    # Simplified Director View reuse
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Students", len(st.session_state.db['students']))
    k2.metric("System", "Online")
    render_syllabus_manager()

def render_tutor():
    st.title("Tutor Dashboard")
    render_syllabus_manager()

# --- MAIN ROUTER ---
if not st.session_state.user:
    render_login()
else:
    with st.sidebar:
        st.title("ISAC CORE")
        st.caption(f"Role: {st.session_state.user['role']}")
        
        # NAVIGATION MENU
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
                # QUIZ VIEW
                st.title(f"Quiz: {st.session_state.active_module['title']}")
                q_dist = st.session_state.get('quiz_dist', {})
                st.caption(f"Adaptive Mode: {q_dist.get('Hard',0)} Hard, {q_dist.get('Medium',0)} Med, {q_dist.get('Easy',0)} Easy")
                
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
                            st.session_state.quiz_active = False
                            st.rerun()
            else:
                render_student()
        elif role == "Director": render_director()
        elif role == "Tutor": render_tutor()