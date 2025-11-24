import streamlit as st
import pdfplumber
import os
import json
from openai import OpenAI
from fpdf import FPDF  # 需要安装 fpdf 库: pip install fpdf

# ==========================================
# 1. 基础配置与工具函数
# ==========================================
st.set_page_config(page_title="简历智能精修", page_icon="🏅", layout="wide")

# 初始化 session_state (用于存储简历内容，实现实时修改)
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []

def get_groq_key():
    """混合鉴权逻辑：优先 Secrets -> 环境变量 -> 侧边栏输入"""
    # 1. 检查 Secrets
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    
    # 2. 检查环境变量
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_API_KEY")

    # 3. 侧边栏输入
    with st.sidebar:
        st.markdown("### 🔑 鉴权")
        user_key = st.text_input("输入 Groq API Key:", type="password")
        if not user_key:
            st.warning("⚠️ 请先配置 API Key")
            st.stop()
        return user_key

def create_pdf(text):
    """简单的 PDF 生成器"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)
    # 处理一些非 Latin 字符可能会报错，这里做简单处理
    try:
        pdf.multi_cell(0, 10, text.encode('latin-1', 'replace').decode('latin-1'))
    except:
        pdf.multi_cell(0, 10, text)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 2. 主界面逻辑
# ==========================================

st.title("🚀 AI 简历精修工作台")

# 获取 Key
api_key = get_groq_key()

# 布局：两列
left_col, right_col = st.columns([1, 1])

# --- 左侧：简历查看与编辑器 ---
with left_col:
    st.header("📄 简历内容 (实时编辑)")
    
    # 文件上传区
    uploaded_file = st.file_uploader("1. 上传简历 (PDF)", type=["pdf"])
    
    # 只有当用户还没解析过，且上传了文件时，才进行解析
    if uploaded_file and not st.session_state.resume_text:
        with pdfplumber.open(uploaded_file) as pdf:
            extracted_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text: extracted_text += text + "\n"
            st.session_state.resume_text = extracted_text
            st.rerun() # 重新加载以显示文字

    # 核心组件：可编辑的文本框
    # 注意：这里的 value 绑定了 session_state，实现实时更新
    current_text = st.text_area(
        "简历文本内容", 
        value=st.session_state.resume_text,
        height=600,
        help="你可以在这里直接手动修改，也可以通过右侧 AI 建议一键修改"
    )
    
    # 如果用户手动改了文本框，同步回 session_state
    if current_text != st.session_state.resume_text:
        st.session_state.resume_text = current_text

    # 下载按钮
    if st.session_state.resume_text:
        st.download_button(
            label="💾 下载修改后的简历 (TXT)",
            data=st.session_state.resume_text,
            file_name="modified_resume.txt",
            mime="text/plain"
        )

# --- 右侧：AI 建议与操作 ---
with right_col:
    st.header("🤖 AI 优化建议")
    
    jd_text = st.text_area("2. 输入职位描述 (JD)", height=150, placeholder="粘贴 JD...")
    
    analyze_btn = st.button("✨ 开始 AI 分析", type="primary", use_container_width=True)
    
    # AI 分析逻辑
    if analyze_btn and api_key and st.session_state.resume_text and jd_text:
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        
        with st.spinner("正在逐句分析简历与 JD 的匹配度..."):
            try:
                # Prompt 设计：强制返回 JSON 格式以便程序处理
                system_prompt = """
                You are a resume expert. Analyze the resume against the JD.
                Identify 3-5 distinct sections or sentences that need improvement.
                
                You MUST return the response in strict JSON format like this:
                {
                    "suggestions": [
                        {
                            "original_text": "text segment from resume",
                            "improved_text": "rewritten version",
                            "reason": "why this change is needed"
                        }
                    ]
                }
                Do not include any other text outside the JSON.
                """
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # 或 mixstral-8x7b-32768
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Resume: {st.session_state.resume_text}\n\nJD: {jd_text}"}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"} # 强制 JSON 模式 (Groq 支持)
                )
                
                # 解析 JSON
                result = json.loads(response.choices[0].message.content)
                st.session_state.suggestions = result.get("suggestions", [])
                
            except Exception as e:
                st.error(f"分析出错: {str(e)}")

    # --- 展示建议列表 (交互核心) ---
    if st.session_state.suggestions:
        st.info(f"💡 发现了 {len(st.session_state.suggestions)} 处优化建议")
        
        for idx, item in enumerate(st.session_state.suggestions):
            with st.expander(f"建议 #{idx+1}: {item['reason'][:30]}...", expanded=True):
                st.markdown(f"**🔴 原文:**")
                st.code(item['original_text'], language="text")
                
                st.markdown(f"**🟢 建议修改:**")
                st.code(item['improved_text'], language="text")
                
                st.markdown(f"_{item['reason']}_")
                
                col_accept, col_ignore = st.columns([1, 1])
                
                # 按钮逻辑：应用修改
                if col_accept.button("✅ 采纳建议", key=f"btn_accept_{idx}"):
                    # Python replace 逻辑
                    if item['original_text'] in st.session_state.resume_text:
                        st.session_state.resume_text = st.session_state.resume_text.replace(
                            item['original_text'], 
                            item['improved_text']
                        )
                        st.success("已修改！左侧文本已更新。")
                        st.rerun() # 强制刷新页面显示新文本
                    else:
                        st.warning("⚠️ 原文在左侧未找到，可能你已经修改过了。")
                
                # 按钮逻辑：忽略 (其实就是不操作，或者可以从列表移除)
                if col_ignore.button("🗑️ 忽略", key=f"btn_ignore_{idx}"):
                    # 这里可以写逻辑从 session_state.suggestions 删除该项
                    pass
