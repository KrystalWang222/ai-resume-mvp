# app.py
import streamlit as st
import os
from openai import OpenAI
# 引入我们刚才分离出去的工具箱
from utils import extract_text_from_pdf, analyze_resume_with_ai, generate_pdf

st.set_page_config(layout="wide", page_title="AI Resume Fixer")

# --- 1. 初始化 Session State (状态记忆) ---
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = [] # 存储 AI 给的建议列表
if 'suggestion_status' not in st.session_state:
    st.session_state.suggestion_status = {} # 记录每个建议的状态: 'pending', 'accepted', 'ignored'

# --- 2. 侧边栏：设置与多语言 ---
with st.sidebar:
    st.header("⚙️ Settings / 设置")
    
    # 多语言切换
    language = st.radio("Language / 语言", ["English", "中文"], horizontal=True)
    lang_code = "en" if language == "English" else "zh"
    
    # API Key 逻辑
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = st.text_input("Groq API Key", type="password")

# --- 3. 界面文本配置 (简单的字典实现多语言) ---
TEXT = {
    "title": {"en": "🚀 AI Resume Tailor", "zh": "🚀 AI 简历精修助手"},
    "upload_header": {"en": "📄 Upload Resume", "zh": "📄 上传简历"},
    "jd_header": {"en": "💼 Job Description", "zh": "💼 职位描述 (JD)"},
    "editor_header": {"en": "📝 Live Editor", "zh": "📝 实时编辑器"},
    "suggestion_header": {"en": "🤖 AI Suggestions", "zh": "🤖 AI 修改建议"},
    "start_btn": {"en": "Analyze Resume", "zh": "开始分析"},
    "download_btn": {"en": "Download PDF", "zh": "下载修改后的 PDF"},
    "no_change": {"en": "Ignored", "zh": "已忽略"},
    "accepted": {"en": "Accepted", "zh": "已采纳"}
}

st.title(TEXT["title"][lang_code])

col1, col2 = st.columns([1, 1])

# --- 左列：编辑器 ---
with col1:
    st.subheader(TEXT["editor_header"][lang_code])
    uploaded_file = st.file_uploader(TEXT["upload_header"][lang_code], type="pdf")
    
    # 解析文件 (只做一次)
    if uploaded_file and not st.session_state.resume_text:
        st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
        st.rerun()

    # 文本编辑器
    current_text = st.text_area(
        "Resume Content", 
        value=st.session_state.resume_text,
        height=600,
        label_visibility="collapsed"
    )
    
    # 同步手动修改的内容
    if current_text != st.session_state.resume_text:
        st.session_state.resume_text = current_text

    # 下载按钮 (PDF)
    if st.session_state.resume_text:
        pdf_bytes = generate_pdf(st.session_state.resume_text)
        st.download_button(
            label=TEXT["download_btn"][lang_code],
            data=pdf_bytes,
            file_name="tailored_resume.pdf",
            mime="application/pdf"
        )

# --- 右列：AI 建议与交互 ---
with col2:
    st.subheader(TEXT["suggestion_header"][lang_code])
    jd_text = st.text_area(TEXT["jd_header"][lang_code], height=150)
    
    if st.button(TEXT["start_btn"][lang_code], type="primary", use_container_width=True):
        if not api_key:
            st.error("Please provide API Key")
        else:
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            with st.spinner("AI is thinking..."):
                # 调用 utils 里的函数
                suggestions = analyze_resume_with_ai(client, st.session_state.resume_text, jd_text, language=lang_code)
                st.session_state.suggestions = suggestions
                # 重置所有建议的状态为 pending
                st.session_state.suggestion_status = {i: 'pending' for i in range(len(suggestions))}

    # --- 渲染建议卡片 ---
    if st.session_state.suggestions:
        # 遍历所有建议
        for idx, item in enumerate(st.session_state.suggestions):
            status = st.session_state.suggestion_status.get(idx, 'pending')
            
            # 如果是 pending (待处理)，显示完整卡片
            if status == 'pending':
                with st.container(border=True):
                    st.markdown(f"**🔴 Original:** `{item['original_text']}`")
                    st.markdown(f"**🟢 Suggestion:** `{item['improved_text']}`")
                    st.caption(f"💡 Reason: {item['reason']}")
                    
                    c1, c2 = st.columns(2)
                    
                    # 采纳按钮
                    if c1.button("✅ Accept", key=f"acc_{idx}", use_container_width=True):
                        # 1. 修改文本
                        if item['original_text'] in st.session_state.resume_text:
                            st.session_state.resume_text = st.session_state.resume_text.replace(item['original_text'], item['improved_text'])
                        # 2. 标记状态
                        st.session_state.suggestion_status[idx] = 'accepted'
                        st.rerun()
                    
                    # 忽略按钮
                    if c2.button("🗑️ Ignore", key=f"ign_{idx}", use_container_width=True):
                        # 1. 标记状态
                        st.session_state.suggestion_status[idx] = 'ignored'
                        st.rerun()

            # 如果已处理 (折叠显示)
            elif status == 'accepted':
                st.info(f"✅ {TEXT['accepted'][lang_code]}: {item['reason'][:20]}...")
            
            elif status == 'ignored':
                # 如果忽略，显示一个小的灰色条，允许用户“反悔”吗？
                # 为了 MVP 简单，我们可以加一个 "Undo" 按钮
                with st.expander(f"🗑️ {TEXT['no_change'][lang_code]} (Click to undo)"):
                    if st.button("Undo / 撤销操作", key=f"undo_{idx}"):
                        st.session_state.suggestion_status[idx] = 'pending'
                        st.rerun()
