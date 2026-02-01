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

# --- 2. ניהול כניסה ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def apply_style(dir, align):
    st.markdown(f"""
    <style>
        .stApp {{ background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d); color: white; direction: {dir}; text-align: {align}; }}
        .main-header {{ background: linear-gradient(90deg, #FFD194, #D1913C); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; font-weight: 900; text-align: center; }}
        div.stButton > button {{ background: linear-gradient(45deg, #FD746C, #FF9068); border-radius: 12px; color: white; border: none; font-weight: bold; width: 100%; height: 3em; }}
        [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.6); }}
        .stTextArea textarea, .stTextInput input {{ background-color: rgba(255, 255, 255, 0.1) !important; color: white !important; border: 1px solid #FD746C !important; }}
    </style>
    """, unsafe_allow_html=True)

# פונקציה לחילוץ טקסט מקבצים
def extract_text(file):
    if file.type == "application/pdf":
        return "\n".join([page.extract_text() for page in PdfReader(file).pages if page.extract_text()])
    elif "wordprocessingml" in file.type:
        return "\n".join([p.text for p in Document(file).paragraphs])
    return None

# --- 3. מסך כניסה ---
if not st.session_state.logged_in:
    apply_style("rtl", "center")
    st.markdown("<h1 class='main-header'>EduCheck Smart 🌅</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        code = st.text_input("Access Code / קוד גישה", type="password")
        if st.button("כניסה 🔑"):
            if code:
                st.session_state.logged_in = True
                st.session_state.teacher_id = code
                st.rerun()
    st.stop()

# --- 4. הגדרות לאחר כניסה ---
selected_lang = st.sidebar.selectbox("🌐 Language / שפה", ["עברית", "English"])
L = LANG_DICT[selected_lang]
apply_style(L["dir"], L["align"])

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key missing in Secrets!")

# יצירת תיקיית מורה
base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path): os.makedirs(base_path)

# --- 5. סיידבר: רישום תלמיד (3 העלאות) ---
with st.sidebar.expander(L["student_reg"]):
    new_name = st.text_input("שם התלמיד המלא:")
    s1 = st.file_uploader("דגימת כתב 1", type=['png', 'jpg', 'jpeg'], key="s1")
    s2 = st.file_uploader("דגימת כתב 2", type=['png', 'jpg', 'jpeg'], key="s2")
    s3 = st.file_uploader("דגימת כתב 3", type=['png', 'jpg', 'jpeg'], key="s3")
    
    if st.button(L["save_btn"]):
        if new_name and s1 and s2 and s3:
            s_path = os.path.join(base_path, new_name)
            if not os.path.exists(s_path): os.makedirs(s_path)
            for i, f in enumerate([s1, s2, s3]):
                Image.open(f).save(os.path.join(s_path, f"sample_{i}.png"))
            st.success(f"התלמיד {new_name} נשמר במערכת!")
            st.rerun()

# --- 6. ממשק עבודה ראשי ---
st.markdown(f"<h1 class='main-header'>{L['title']}</h1>", unsafe_allow_html=True)
st.divider()

students = sorted(os.listdir(base_path))

if not students:
    st.info("ברוכים הבאים! התחילו ברישום תלמיד חדש בסרגל הצד.")
else:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader(L["select_student"])
        target_student = st.selectbox("", students, label_visibility="collapsed")
        st.write(L["exam_type"])
        exam_kind = st.radio("", L["types"], label_visibility="collapsed")
        
    with col2:
        st.subheader(L["upload_label"])
        # אפשרות להעלאת קובץ
        file_up = st.file_uploader("בחר קובץ", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])
        # אפשרות לצילום ישיר
        img_cam = st.camera_input("או צלם את המבחן עכשיו")
        
    with col3:
        st.subheader(L["rubric_label"])
        rubric_text = st.text_area("", placeholder="הכנס את התשובות הנכונות כאן...", height=200)

    if st.button(L["btn_check"]):
        exam_source = img_cam if img_cam else file_up
        if exam_source and rubric_text:
            with st.status(L["scan_msg"]):
                try:
                    s_dir = os.path.join(base_path, target_student)
                    # טעינת דגימות לכיול
                    samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir) if f.startswith("sample_")]
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Grade this {exam_kind} exam for {target_student}. Compare with rubric: {rubric_text}. Use the 3 handwriting samples to calibrate OCR. Respond in {selected_lang}."
                    
                    inputs = [prompt] + samples
                    
                    # בדיקה אם זה קובץ טקסט או תמונה/צילום
                    if hasattr(exam_source, 'type') and exam_source.type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                        extracted = extract_text(exam_source)
                        inputs.append(f"Content from Document: {extracted}")
                    else:
                        inputs.append(Image.open(exam_source))
                    
                    # שמירת המבחן להיסטוריה של התלמיד
                    with open(os.path.join(s_dir, f"last_check_saved.png"), "wb") as f:
                        f.write(exam_source.getbuffer())

                    response = model.generate_content(inputs)
                    st.balloons()
                    st.markdown("### 📋 סיכום הבדיקה:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה בתהליך: {e}")
        else:
            st.warning("נא להעלות מבחן ולהזין מחוון!")
