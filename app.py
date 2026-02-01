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

# --- 3. מילון שפות מורחב וכיווניות ---
LANG_CONFIG = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EduCheck Smart 🌅", "login_msg": "הזן קוד מורה:", "login_btn": "התחבר", "reg_header": "📝 רישום תלמיד חדש", "name_label": "שם מלא:", "sample_label": "דגימת כתב יד", "save_btn": "שמור תלמיד", "select_student": "בחר תלמיד:", "exam_type": "סוג מטלה:", "rubric_label": "מחוון תשובות:", "upload_label": "העלאת עבודה (תמונה/PDF/Word/צילום)", "check_btn": "בצע בדיקה חכמה 🚀", "types": ["מבחן פתוח", "אמריקאי", "השלמה", "מתמטיקה"]},
    "English": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "Enter Teacher Code:", "login_btn": "Login", "reg_header": "📝 Register Student", "name_label": "Full Name:", "sample_label": "Handwriting Sample", "save_btn": "Save Student", "select_student": "Select Student:", "exam_type": "Exam Type:", "rubric_label": "Answer Rubric:", "upload_label": "Upload Work (Img/PDF/Word/Camera)", "check_btn": "Start Analysis 🚀", "types": ["Open", "Multiple Choice", "Blanks", "Math"]},
    "العربية": {"dir": "rtl", "align": "right", "title": "EduCheck Smart 🌅", "login_msg": "أدخل رمز المعلم:", "login_btn": "تسجيل الدخول", "reg_header": "📝 تسجيل طالب جديد", "name_label": "الاسم الكامل:", "sample_label": "عينة خط اليد", "save_btn": "حفظ الطالب", "select_student": "اختر طالب:", "exam_type": "نوع الامتحان:", "rubric_label": "نموذج الإجابة:", "upload_label": "تحميل العمل (صورة/PDF/Word/كاميرا)", "check_btn": "ابدأ التحليل الذكي 🚀", "types": ["مفتوح", "اختيار من متعدد", "إكمال", "رياضيات"]},
    "Français": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "Code Enseignant:", "login_btn": "Connexion", "reg_header": "📝 Créer un Étudiant", "name_label": "Nom Complet:", "sample_label": "Échantillon d'écriture", "save_btn": "Enregistrer", "select_student": "Choisir Étudiant:", "exam_type": "Type d'examen:", "rubric_label": "Corrigé:", "upload_label": "Charger Travail (Img/PDF/Word/Caméra)", "check_btn": "Analyser 🚀", "types": ["Ouvert", "QCM", "Lacunaire", "Maths"]},
    "Español": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "Código del Profesor:", "login_btn": "Entrar", "reg_header": "📝 Registrar Estudiante", "name_label": "Nombre Completo:", "sample_label": "Muestra de escritura", "save_btn": "Guardar", "select_student": "Elegir Estudiante:", "exam_type": "Tipo de examen:", "rubric_label": "Clave de respuestas:", "upload_label": "Subir Trabajo (Img/PDF/Word/Cámara)", "check_btn": "Analizar 🚀", "types": ["Abierto", "Opción Múltiple", "Completar", "Matemáticas"]},
    "中文": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "输入教师代码:", "login_btn": "登录", "reg_header": "📝 注册新学生", "name_label": "姓名:", "sample_label": "手写样本", "save_btn": "保存学生", "select_student": "选择学生:", "exam_type": "考试类型:", "rubric_label": "评分标准/答案:", "upload_label": "上传作业 (图片/PDF/Word/相机)", "check_btn": "开始智能分析 🚀", "types": ["问答题", "选择题", "填空题", "数学"]}
}

# בחירת שפה (בסיידבר)
lang_choice = st.sidebar.selectbox("🌐 Language / שפה", list(LANG_CONFIG.keys()))
L = LANG_CONFIG[lang_choice]

# --- 4. עיצוב דינמי (תיקון שגיאת ה-f-string) ---
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
        code = st.text_input("Code", type="password")
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
    st.error("Missing API Key in Secrets!")
    st.stop()

base_path = f"data_{st.session_state.teacher_id}"
if not os.path.exists(base_path): 
    os.makedirs(base_path)

# פונקציית חילוץ טקסט
def extract_text(file):
    try:
        if file.type == "application/pdf":
            return "\n".join([page.extract_text() for page in PdfReader(file).pages if page.extract_text()])
        elif "wordprocessingml" in file.type:
            return "\n".join([p.text for p in Document(file).paragraphs])
    except: return None
    return None

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
    st.warning("Please register a student in the sidebar.")
else:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        target = st.selectbox(L["select_student"], students)
        e_type = st.radio(L["exam_type"], L["types"])
        rubric = st.text_area(L["rubric_label"], height=200)

    with c2:
        st.subheader(L["upload_label"])
        file_up = st.file_uploader("", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])
        cam_up = st.camera_input("")

    if st.button(L["check_btn"]):
        source = cam_up if cam_up else file_up
        if source and rubric:
            with st.spinner("Analyzing handwriting based on samples..."):
                try:
                    s_dir = os.path.join(base_path, target)
                    samples = [Image.open(os.path.join(s_dir, f)) for f in os.listdir(s_dir) if f.startswith("sample_")]
                    
                    # הנחיה ל-AI: שימוש בלעדי בדגימות כתב היד שהועלו
                    prompt = f"""
                    Professional Teacher Role. 
                    Task: Grade the student '{target}''s work.
                    
                    HANDWRITING RULES:
                    1. Use ONLY the 3 handwriting samples provided for this student as your reference.
                    2. Do not use generic OCR. Match the strokes and letter shapes in the exam to the samples.
                    
                    GRADING:
                    Compare the decoded text to this rubric: {rubric}.
                    
                    LANGUAGE:
                    Respond in {lang_choice}.
                    """
                    
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    inputs = [prompt] + samples
                    
                    if hasattr(source, 'type') and ("pdf" in source.type or "word" in source.type):
                        inputs.append(f"Document Context: {extract_text(source)}")
                    else:
                        inputs.append(Image.open(source))
                    
                    response = model.generate_content(inputs)
                    st.balloons()
                    st.markdown("---")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")
