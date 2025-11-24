# utils.py
import pdfplumber
from fpdf import FPDF
from openai import OpenAI
import json

# ===========================
# 1. 核心业务逻辑：分析简历
# ===========================
def analyze_resume_with_ai(client, resume_text, jd_text, model="llama-3.3-70b-versatile", language="en"):
    
    # 根据语言选择 Prompt 语言
    lang_instruction = "Respond in English." if language == "en" else "Respond in Chinese (Simplified)."

    system_prompt = f"""
    You are a strictly factual Senior Recruiter. {lang_instruction}
    
    Your Goal: Optimize the candidate's resume keywords to match the JD, BUT you must adhere to the following STRICT RULES:
    
    1. 🚫 **NO HALLUCINATIONS**: Do NOT invent skills, certifications, or experiences that are not present in the Resume.
    2. 🚫 **NO TITLE INFLATION**: Do NOT change the candidate's job titles (e.g., do not change "Junior" to "Senior").
    3. ✅ **TRUTH ONLY**: Only rephrase existing bullet points to sound more professional or to match JD keywords.
    4. ✅ **Constructive Feedback**: If the candidate lacks a hard skill required by the JD, do NOT add it. Instead, suggest in the "reason" field that they should learn it.

    You MUST return the response in strict JSON format like this:
    {{
        "suggestions": [
            {{
                "original_text": "exact sentence from resume",
                "improved_text": "rewritten version",
                "reason": "Explain why (e.g., 'Added metric', 'Matched JD keyword: Python')"
            }}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Resume Content:\n{resume_text}\n\nJob Description:\n{jd_text}"}
            ],
            temperature=0.1, # 降低温度，越低越严谨，越不会乱编
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content).get("suggestions", [])
    except Exception as e:
        return []

# ===========================
# 2. PDF 生成工具
# ===========================
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # 注意：标准 FPDF 不支持中文字体。为了 MVP 简单，我们先用 Arial。
    # 如果要支持中文下载，需要上传 .ttf 字体文件，这里先做英文版兜底。
    pdf.set_font("Arial", size=11)
    
    # 简单的处理，防止编码报错
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, safe_text)
    return pdf.output(dest='S').encode('latin-1')

# ===========================
# 3. PDF 解析工具
# ===========================
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text
