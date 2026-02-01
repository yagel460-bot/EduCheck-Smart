import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from docx import Document
from PyPDF2 import PdfReader

# --- 1. הגדרות דף ---
st.set_page_config(page_title="EduCheck Smart", layout="wide", page_icon="🌅")

# --- 2. ניהול מצב (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

# --- 3. מילון שפות וכיווניות ---
LANG_CONFIG = {
    "עברית": {
        "dir": "rtl",
        "align": "right",
        "title": "EduCheck Smart 🌅",
        "login_msg": "אנא הזן קוד מורה כדי לטעון את המאגר שלך:",
        "login_btn": "התחבר",
        "reg_header": "📝 רישום תלמיד חדש",
        "name_label": "שם מלא:",
        "sample_label": "דגימת כתב יד",
        "save_btn": "שמור תלמיד",
        "select_student": "בחר תלמיד:",
        "exam_type": "סוג המטלה:",
        "rubric_label": "מחוון תשובות (מה התשובה הנכונה?):",
        "upload_label": "העלאת עבודת התלמיד (תמונה/PDF/Word/צילום)",
        "check_btn": "בצע בדיקה חכמה 🚀",
        "types": ["מבחן פתוח", "אמריקאי", "השלמת משפטים", "מתמטיקה"]
    },
    "English": {
        "dir": "ltr",
        "align": "left",
        "title": "EduCheck Smart 🌅",
        "login_msg": "Please enter teacher code to load your database:",
        "login_btn": "Login",
        "reg_header": "📝 Register New Student",
        "name_label": "Full Name:",
        "sample_label": "Handwriting Sample",
        "save_btn": "Save Student",
        "select_student": "Select Student:",
        "exam_type": "Exam Type:",
        "rubric_label": "Answer Rubric (What is the correct answer?):",
        "upload_label": "Upload Student Work (Img/PDF/Word/Camera)",
        "check_btn": "Start Smart Analysis 🚀",
        "types": ["Open Exam", "Multiple Choice", "Fill in Blanks", "Math"]
    }
}

# בחירת שפה בסיידבר (תמיד זמין)
lang_choice = st.sidebar.selectbox("🌐 Language / שפה", ["עברית", "English"])
L = LANG_CONFIG[lang_choice]

# --- 4. עיצוב דינמי (מתאים את עצמו לימין/שמאל) ---
def apply_custom_style():
    st.markdown(f"""
    <style>
        .stApp {{ 
            background-color: #ffffff; 
            color: #1e1e1e; 
            direction: {L['dir']}; 
            text-align: {L['align']}; 
        }}
        .main-header {{ 
            color: #2c3e50; 
            font-size: 3rem; 
            font-weight: 800; 
            text-align: center; 
            padding: 1rem;
            border-bottom: 2px solid #f0f2f6;
        }}
        /* תיקון כיווניות לסיידבר */
        [data-testid="stSidebar"] {{ 
            background-color: #f0f2f6; 
            direction: {L['dir']};
        }}
        .stButton > button {{ 
            background: #4a90e2; 
            color: white; 
            border-radius: 10px; 
            font-weight: bold;
            width: 100%;
        }}
        .stTextInput input, .stTextArea textarea {{ 
            text-align: {L['align']};
            direction: {L['dir']};
        }}
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- 5. מסך כניסה ---
if not st.session_state.logged_in:
    st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.info(L["login_msg"])
        code = st.text_input("Teacher Code", type="password")
        if st.button(L["login_btn"]):
            if code:
                st.session_state.logged_in = True
                st.session_state.teacher_id = code
                st.rerun()
    st.stop()

# --- 6. הגדרת API ותיקיות ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key!")
    st.stop()

base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path):
    os.makedirs(base_path)

# --- 7. סיידבר: רישום תלמיד ---
with st.sidebar:
    st.header(L["reg_header"])
    new_name = st.text_input(L["name_label"])
    s1 = st.file_uploader(f"{L['sample_label']} 1", type=['png', 'jpg', 'jpeg'], key="u1")
    s2 = st.file_uploader(f"{L['sample_label']} 2", type=['png', 'jpg', 'jpeg'], key="u2")
    s3 = st.file_uploader(f"{L['sample_label']} 3", type=['png', 'jpg', 'jpeg'], key="u3")
    
    if st.button(L["save_btn"]):
        if new_name and s1 and s2 and s3:
            s_path = os.path.join(base_path, new_name)
            if not os.path.exists(s_path): os.makedirs(s_path)
            for i, f in enumerate([s1, s2, s3]):
                Image.open(f).save(os.path.join(s_path, f"sample_{i}.png"))
            st.success("V")
            st.rerun()

# --- 8. ממשק בדיקה ראשי ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)

students = sorted(os.listdir(base_path))
if not students:
    st.warning("No students registered.")
else:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        target = st.selectbox(L["select_student"], students)
        e_type = st.radio(L["exam_type"], L["types"])
        rubric = st.text_area(L["rubric_label"], height=200)

    with c2:
        st.subheader(L["upload_label"])
        exam_img = st.file_uploader("", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])
        exam_cam = st.camera_input("")

    if st.button(L["check_btn"]):
        exam_source = exam_cam if exam_cam else exam_img
        if exam_source and rubric:
            with st.spinner("Analyzing..."):
                try:
                    s_dir = os.path.join(base_path, target)
                    samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir) if f.startswith("sample_")]
                    
                    # הנחיה ל-AI: התמקדות מוחלטת בדגימות כתב היד
                    prompt = f"""
                    You are a professional teacher. Grade the exam for student: {target}.
                    
                    CRITICAL INSTRUCTION:
                    Analyze the student's handwriting based ONLY on the 3 provided samples. 
                    Identify the letters and numbers based on this student's specific style shown in the samples.
                    Compare the identified text to this rubric: {rubric}.
                    
                    Respond in {lang_choice}.
                    """
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    inputs = [prompt] + samples
                    
                    if hasattr(exam_source, 'type') and exam_source.type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                        # (פונקציית חילוץ טקסט כאן...)
                        inputs.append("Document Text Context")
                    else:
                        inputs.append(Image.open(exam_source))
                    
                    response = model.generate_content(inputs)
                    st.balloons()
                    st.markdown("---")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")
