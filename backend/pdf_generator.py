import os
import subprocess
from docxtpl import DocxTemplate

GENERATED_FOLDER = os.path.join(os.path.dirname(__file__), 'generated')
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates', 'leave_template.docx')

def generate_document(data):
    """توليد ملف Word ثم تحويله إلى PDF باستخدام LibreOffice"""
    
    # التأكد من وجود مجلد generated
    os.makedirs(GENERATED_FOLDER, exist_ok=True)
    
    national_id = data.get('national_id', 'unknown')
    
    # تعبئة قالب Word
    doc = DocxTemplate(TEMPLATE_PATH)
    doc.render(data)
    
    # حفظ ملف Word
    word_path = os.path.join(GENERATED_FOLDER, f"{national_id}.docx")
    doc.save(word_path)
    
    # مسار ملف PDF النهائي
    pdf_path = os.path.join(GENERATED_FOLDER, f"{national_id}.pdf")
    
    # استخدام LibreOffice للتحويل
    libreoffice_path = "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
    
    if os.path.exists(libreoffice_path):
        subprocess.run([
            libreoffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", GENERATED_FOLDER,
            word_path
        ], capture_output=True)
        
        # حذف ملف Word المؤقت (اختياري)
        # os.remove(word_path)
        
        return pdf_path
    else:
        # إذا لم يوجد LibreOffice، أرجع ملف Word فقط
        return word_path