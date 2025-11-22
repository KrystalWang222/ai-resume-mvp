import streamlit as st
import pdfplumber
import os
from openai import OpenAI

# 页面配置
st.set_page_config(page_title="简历修改工具", page_icon="🚀", layout="wide")

st.title("🚀 AI 简历修改工具 (Groq 版)")

# ==========================================
# 🔑 侧边栏：直接输入 Groq Key
# ==========================================
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("在此输入 Groq API Key", type="password", help="以 gsk_ 开头的 Key")
    st.markdown("[👉 点击这里申请 Groq Key](https://console.groq.com/keys)")
    st.markdown("---")
    st.info("💡 Groq 速度极快且目前免费")

# ==========================================
# 主界面逻辑
# ==========================================

st.markdown("---")
left_col, right_col = st.columns(2)

with left_col:
    st.header("📤 简历上传")
    uploaded_file = st.file_uploader("上传 PDF 简历", type=["pdf"])
    
    resume_text = ""
    if uploaded_file:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: resume_text += text + "\n"
            if resume_text:
                st.success(f"✅ 提取成功: {len(resume_text)} 字")
        except Exception as e:
            st.error(f"❌ 读取出错: {e}")

    job_description = st.text_area("输入职位描述 (JD)", height=200, placeholder="粘贴 JD 内容...")
    start_btn = st.button("🚀 开始修改", type="primary", use_container_width=True)

with right_col:
    st.header("📝 修改建议")
    
    if start_btn:
        if not api_key:
            st.error("❌ 请先在左侧输入 Groq API Key")
        elif not uploaded_file:
            st.error("❌ 请上传简历")
        elif not job_description:
            st.error("❌ 请输入 JD")
        else:
            try:
                # 初始化 Groq 客户端
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.groq.com/openai/v1"
                )

                with st.spinner("⚡️ Analyzing and tailoring your resume..."):
                    response = client.chat.completions.create(
                        # 保持使用最新的 Llama 3.3
                        model="llama-3.3-70b-versatile",
                        messages=[
                            # 🔴 核心修改：把 System Prompt 改成专业的英文指令
                            {"role": "system", "content": """You are an expert Senior Recruiter and Career Coach. 
                            Your task is to analyze the candidate's Resume against the provided Job Description (JD).

                            Please provide your output strictly in **English** and use Markdown formatting. 
                            
                            Your output should include:
                            1. 📊 **Match Analysis**: A brief assessment of how well the resume fits the role.
                            2. ⚠️ **Skill Gaps**: Key keywords or skills from the JD that are missing in the resume.
                            3. ✍️ **Rewritten Experience**: Rewrite the top 3 most relevant bullet points from the resume to better align with the JD keywords. Use strong action verbs and metrics.
                            4. 💡 **Optimization Tips**: Specific, actionable advice to improve the resume's ATS score.
                            """},
                            
                            # 用户的输入部分保持不变
                            {"role": "user", "content": f"Resume Content:\n{resume_text}\n\nJob Description:\n{job_description}"}
                        ],
                        temperature=0.7
                    )
                    st.markdown(response.choices[0].message.content)
                    
            except Exception as e:
                st.error(f"❌ 发生错误: {e}")
                st.warning("请检查 Key 是否正确，或是否以 gsk_ 开头")
