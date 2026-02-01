import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from docx import Document
from PyPDF2 import PdfReader

# --- 1. הגדרות דף ושפה ---
st.set_page_config(page_title="EduCheck Smart", layout="wide", page_icon="🌅")

# --- 2. ניהול מצב (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

# --- 3. עיצוב "בוקר בהיר" קריא ---
def apply_style():
    st.markdown("""
    <style>
        .stApp { background-color: #ffffff; color: #1e1e1e; }
        .main-header { 
            color: #2c3e50; 
            font-size: 3rem; 
            font-weight: 800; 
            text-align: center; 
            padding: 1rem;
            border-bottom: 2px solid #f0f2f6;
        }
        .stButton > button { 
            background: #4a90e2; 
            color: white; 
            border-radius: 10px; 
            height: 3em; 
            width: 100%;
            font-weight: bold;
        }
        .stTextInput input, .stTextArea textarea { 
            background-color: #f9f9f9 !important; 
            color: black !important; 
            border: 1px solid #ddd !important; 
        }
        [data-testid="stSidebar"] { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# פונקציה לחילוץ טקסט
def extract_text(file):
    try:
        if file.type == "application/pdf":
            return "\n".join([page.extract_text() for page in PdfReader(file).pages if page.extract_text()])
        elif "wordprocessingml" in file.type:
            return "\n".join([p.text for p in Document(file).paragraphs])
    except: return None
    return None

# --- 4. מסך כניסה ---
if not st.session_state.logged_in:
    apply_style()
    st.markdown("<h1 class='main-header'>EduCheck Smart 🌅</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.info("אנא הזן קוד מורה כדי לטעון את מאגר התלמידים שלך.")
        code = st.text_input("Access Code", type="password")
        if st.button("התחבר"):
            if code:
                st.session_state.logged_in = True
                st.session_state.teacher_id = code
                st.rerun()
    st.stop()

# --- 5. ממשק ראשי ---
apply_style()
st.markdown("<h1 class='main-header'>EduCheck Smart 🌅</h1>", unsafe_allow_html=True)

# הגדרת ה-API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key in Secrets!")
    st.stop()

# יצירת/טעינת תיקיית מורה
base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path):
    os.makedirs(base_path)

# סיידבר: רישום תלמיד
with st.sidebar:
    st.header("📝 רישום תלמיד חדש")
    new_name = st.text_input("שם מלא:")
    s1 = st.file_uploader("דגימת כתב 1 (אותיות/מספרים)", type=['png', 'jpg', 'jpeg'], key="u1")
    s2 = st.file_uploader("דגימת כתב 2 (משפטים)", type=['png', 'jpg', 'jpeg'], key="u2")
    s3 = st.file_uploader("דגימת כתב 3 (חתימה/טקסט חופשי)", type=['png', 'jpg', 'jpeg'], key="u3")
    
    if st.button("שמור תלמיד במערכת"):
        if new_name and s1 and s2 and s3:
            s_path = os.path.join(base_path, new_name)
            if not os.path.exists(s_path): os.makedirs(s_path)
            for i, f in enumerate([s1, s2, s3]):
                Image.open(f).save(os.path.join(s_path, f"sample_{i}.png"))
            st.success(f"התלמיד {new_name} נשמר!")
            st.rerun()

# אזור הבדיקה
students = sorted(os.listdir(base_path))
if not students:
    st.warning("אין תלמידים רשומים במאגר שלך. השתמש בסרגל הצד.")
else:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        target = st.selectbox("בחר תלמיד:", students)
        e_type = st.radio("סוג המטלה:", ["מבחן פתוח", "אמריקאי", "השלמת משפטים", "מתמטיקה"])
        rubric = st.text_area("מחוון תשובות (מה התשובה הנכונה?):", height=200)

    with c2:
        st.subheader("העלאת עבודת התלמיד")
        exam_img = st.file_uploader("העלה תמונה/PDF/Word", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])
        exam_cam = st.camera_input("או צלם עכשיו")

    if st.button("בצע בדיקה חכמה 🚀"):
        exam_source = exam_cam if exam_cam else exam_img
        if exam_source and rubric:
            with st.spinner("מנתח את הכתב לפי דגימות המקור..."):
                try:
                    s_dir = os.path.join(base_path, target)
                    samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir) if f.startswith("sample_")]
                    
                    # הפרומפט החדש - מתרכז במחוון האותיות האישי
                    prompt = f"""
                    You are an expert handwriting analyst and teacher. 
                    TASK: Grade the student's exam based on the provided rubric.
                    
                    STRICT RULES:
                    1. Use ONLY the 3 provided handwriting samples as your reference for how this specific student ('{target}') writes letters and numbers. 
                    2. DO NOT use general OCR models or external knowledge of handwriting. Focus on this student's unique patterns.
                    3. Compare the handwritten exam image to the rubric: {rubric}.
                    4. Identify the text, check for correctness, and give a score.
                    
                    Respond clearly in Hebrew.
                    """
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    inputs = [prompt] + samples
                    
                    if hasattr(exam_source, 'type') and exam_source.type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                        inputs.append(f"Document Text Content: {extract_text(exam_source)}")
                    else:
                        inputs.append(Image.open(exam_source))
                    
                    response = model.generate_content(inputs)
                    st.balloons()
                    st.markdown("---")
                    st.markdown(f"### תוצאות עבור {target}:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה: {e}")
