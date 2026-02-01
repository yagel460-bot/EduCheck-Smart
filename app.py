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

# --- 3. מילון שפות מורחב (עברית, אנגלית, ערבית, צרפתית, ספרדית, סינית) ---
LANG_CONFIG = {
    "עברית": {"dir": "rtl", "align": "right", "title": "EduCheck Smart 🌅", "login_msg": "הזן קוד מורה:", "login_btn": "התחבר", "reg_header": "📝 רישום תלמיד חדש", "name_label": "שם מלא:", "sample_label": "דגימת כתב יד", "save_btn": "שמור תלמיד", "select_student": "בחר תלמיד:", "exam_type": "סוג מטלה:", "rubric_label": "מחוון תשובות:", "upload_label": "העלאת עבודה (תמונה/PDF/Word/צילום)", "check_btn": "בצע בדיקה חכמה 🚀", "types": ["מבחן פתוח", "אמריקאי", "השלמה", "מתמטיקה"]},
    "English": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "Enter Teacher Code:", "login_btn": "Login", "reg_header": "📝 Register Student", "name_label": "Full Name:", "sample_label": "Handwriting Sample", "save_btn": "Save Student", "select_student": "Select Student:", "exam_type": "Exam Type:", "rubric_label": "Answer Rubric:", "upload_label": "Upload Work (Img/PDF/Word/Camera)", "check_btn": "Start Analysis 🚀", "types": ["Open", "Multiple Choice", "Blanks", "Math"]},
    "العربية": {"dir": "rtl", "align": "right", "title": "EduCheck Smart 🌅", "login_msg": "أدخل رمز المعلم:", "login_btn": "تسجيل الدخول", "reg_header": "📝 تسجيل طالب جديد", "name_label": "الاسم الكامل:", "sample_label": "עينة خط اليد", "save_btn": "حفظ الطالب", "select_student": "اخטר طالب:", "exam_type": "نوع الامتحان:", "rubric_label": "نموذج الإجابة:", "upload_label": "تحميل العمل (صورة/PDF/Word/كاميرا)", "check_btn": "ابدأ التحليل الذكي 🚀", "types": ["مفتوح", "اختيار من متعدد", "إكمال", "رياضيات"]},
    "Français": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "Code Enseignant:", "login_btn": "Connexion", "reg_header": "📝 Créer un Étudiant", "name_label": "Nom Complet:", "sample_label": "Échantillon d'écriture", "save_btn": "Enregistrer", "select_student": "Choisir Étudiant:", "exam_type": "Type d'examen:", "rubric_label": "Corrigé:", "upload_label": "Charger Travail (Img/PDF/Word/Caméra)", "check_btn": "Analyser 🚀", "types": ["Ouvert", "QCM", "Lacunaire", "Maths"]},
    "Español": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "Código del Profesor:", "login_btn": "Entrar", "reg_header": "📝 Registrar Estudiante", "name_label": "Nombre Completo:", "sample_label": "Muestra de escritura", "save_btn": "Guardar", "select_student": "Elegir Estudiante:", "exam_type": "Tipo de examen:", "rubric_label": "Clave de respuestas:", "upload_label": "Subir Trabajo (Img/PDF/Word/Cámara)", "check_btn": "Analizar 🚀", "types": ["Abierto", "Opción Múltiple", "Completar", "Matemáticas"]},
    "中文": {"dir": "ltr", "align": "left", "title": "EduCheck Smart 🌅", "login_msg": "输入教师代码:", "login_btn": "登录", "reg_header": "📝 注册新学生", "name_label": "姓名:", "sample_label": "手写样本", "save_btn": "保存学生", "select_student": "选择学生:", "exam_type": "考试类型:", "rubric_label": "评分标准/答案:", "upload_label": "上传作业 (图片/PDF/Word/相机)", "check_btn": "开始智能分析 🚀", "types": ["问答题", "选择题", "填空题", "数学"]}
}

# בחירת שפה
lang_choice = st.sidebar.selectbox("🌐 Language / שפה", list(LANG_CONFIG.keys()))
L = LANG_CONFIG[lang_choice]

# --- 4. עיצוב דינמי (RTL/LTR) ---
def apply_custom_style():
    st.markdown(f"""
    <style>
        .stApp {{ background-color: #ffffff; color: #1e1e1e; direction: {L['dir']}; text-align: {L['align']}; }}
        .main-header {{ color: #2c3e50; font-size: 3rem; font-weight: 800; text-align: center; padding: 1rem; border-bottom: 2px solid #f0f2f6; }}
        [data-testid="stSidebar"] {{ background-color: #f0f2f
