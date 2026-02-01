import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from docx import Document
from PyPDF2 import PdfReader

# --- 1. הגדרות דף ושפה ---
st.set_page_config(page_title="EduCheck Smart", layout="wide", page_icon="🌅")

LANG_DICT = {
    "עברית": {
        "dir": "rtl", "align": "right", "title": "EduCheck Smart 🌅",
        "welcome": "ברוכים הבאים", "login_btn": "כניסה למערכת 🔑",
        "student_reg": "📝 רישום תלמיד חדש", "save_btn": "שמור במאגר",
        "select_student": "👤 בחר תלמיד קיים:", "exam_type": "📝 סוג מבחן:",
        "types": ["מבחן פתוח", "מבחן אמריקאי", "השלמת משפטים", "נכון/לא נכון", "מתמטיקה"],
        "upload_label": "📸 העלאת מבחן (תמונה/PDF/Word/צילום)",
        "rubric_label": "🎯 מחוון תשובות", "btn_check": "התחל בדיקת מומחה 🚀",
        "scan_msg": "מנתח נתונים ושומר קבצים..."
    },
    "English": {
        "dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅",
        "welcome": "Welcome", "login_btn": "Login 🔑",
        "student_reg": "📝 Register New Student", "save_btn": "Save to DB",
        "select_student": "👤 Select Student:", "exam_type": "📝 Exam Type:",
        "types": ["Open Question", "Multiple Choice", "Fill in Blanks", "True/False", "Math"],
        "upload_label": "📸 Upload/Camera (Img/PDF/Word)",
        "rubric_label": "🎯 Rubric", "btn_check": "Start Smart Analysis 🚀",
        "scan_msg": "Processing and saving..."
    }
}

# --- 2. ניהול מצב (Session State) - תיקון השגיאה ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

# --- 3. עיצוב בהיר וקריא (Light Mode Edition) ---
def apply_style(dir, align):
    st.markdown(f"""
    <style>
        /* רקע בהיר וטקסט כהה לקריאות מקסימלית */
        .stApp {{
            background-color: #f8f9fa;
            color: #212529;
            direction: {dir};
            text-align: {align};
        }}
        /* כותרת מרשימה אך בהירה */
        .main-header {{
            background: linear-gradient(90deg, #2c3e50, #4ca1af);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3.5rem;
            font-weight: 900;
            text-align: center;
            padding: 20px;
        }}
        /* כפתורים בולטים */
        div.stButton > button {{
            background: linear-gradient(45deg, #4ca1af, #2c3e50);
            border-radius: 8px;
            color: white !important;
            border: none;
            font-weight: bold;
            width: 100%;
            height: 3.5em;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        /* שדות קלט ברורים */
        .stTextArea textarea, .stTextInput input {{
            background-color: white !important;
            color: #212529 !important;
            border: 1px solid #ced4da !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: #ffffff;
            border-right: 1px solid #dee2e6;
        }}
        .stMarkdown p, .stMarkdown h3 {{
            color: #212529 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def extract_text(file):
    try:
        if file.type == "application/pdf":
            return "\n".join([page.extract_text() for page in PdfReader(file).pages if page.extract_text()])
        elif "wordprocessingml" in file.type:
            return "\n".join([p.text for p in Document(file).paragraphs])
    except:
        return None
    return None

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    apply_style("rtl", "center")
    st.markdown("<h1 class='main-header'>EduCheck Smart 🌅</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div style='background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        code = st.text_input("Access Code / קוד גישה", type="password")
        if st.button("כניסה למערכת 🔑"):
            if code:
                st.session_state.logged_in = True
                st.session_state.teacher_id = code
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. הגדרות לאחר כניסה ---
selected_lang = st.sidebar.selectbox("🌐 שפה / Language", ["עברית", "English"])
L = LANG_DICT[selected_lang]
apply_style(L["dir"], L["align"])

# יצירת תיקיית מורה (בדיקה בטוחה שהמשתנה קיים)
if st.session_state.teacher_id:
    base_path = f"data_{st.session_state.teacher_id}"
    if not os.path.exists(base_path): 
        os.makedirs(base_path)
else:
    st.error("ארעה שגיאה בגישה לנתונים. אנא התחבר מחדש.")
    st.stop()

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key missing in Secrets!")

# --- 6. סיידבר: רישום תלמיד ---
with st.sidebar.expander(L["student_reg"]):
    new_name = st.text_input("שם התלמיד:")
    s1 = st.file_uploader("דגימת כתב 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("דגימת כתב 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("דגימת כתב 3", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.button(L["save_btn"]):
        if new_name and s1 and s2 and s3:
            s_path = os.path.join(base_path, new_name)
            if not os.path.exists(s_path): os.makedirs(s_path)
            for i, f in enumerate([s1, s2, s3]):
                Image.open(f).save(os.path.join(s_path, f"sample_{i}.png"))
            st.success(f"נשמר: {new_name}")
            st.rerun()

# --- 7. ממשק ראשי ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
students = sorted(os.listdir(base_path))

if not students:
    st.info("אנא רשום תלמיד בסיידבר כדי להתחיל.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(L["select_student"])
        target_student = st.selectbox("", students, label_visibility="collapsed")
        st.write(L["exam_type"])
        exam_kind = st.radio("", L["types"], label_visibility="collapsed")
    with col2:
        st.subheader(L["upload_label"])
        file_up = st.file_uploader("בחר קובץ (PDF/Word/תמונה)", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])
        img_cam = st.camera_input("או צלם מבחן")
    with col3:
        st.subheader(L["rubric_label"])
        rubric_text = st.text_area("", placeholder="הכנס מחוון...", height=200)

    if st.button(L["btn_check"]):
        exam_source = img_cam if img_cam else file_up
        if exam_source and rubric_text:
            with st.status(L["scan_msg"]):
                try:
                    s_dir = os.path.join(base_path, target_student)
                    samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir) if f.startswith("sample_")]
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Grade this {exam_kind} exam for {target_student}. Use rubric: {rubric_text}. Compare handwriting with samples. Respond in {selected_lang}."
                    
                    inputs = [prompt] + samples
                    if hasattr(exam_source, 'type') and exam_source.type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                        inputs.append(f"Content: {extract_text(exam_source)}")
                    else:
                        inputs.append(Image.open(exam_source))
                    
                    response = model.generate_content(inputs)
                    st.balloons()
                    st.markdown("### ✅ תוצאות בדיקה:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")
