import streamlit as st
import pdfplumber
import google.generativeai as genai

# 页面配置
st.set_page_config(
    page_title="简历修改工具",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI 简历修改工具")

# ==========================================
# 🔑 核心改动：直接在侧边栏输入 Key
# ==========================================
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("在此输入 Google API Key", type="password", help="请粘贴以 AIza 开头的 Key")
    
    st.markdown("---")
    st.info("🔑 Key 将仅用于本次会话，不会存储")

# 配置 Google API
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Key 配置出错: {e}")

# ==========================================
# 下面是主界面逻辑 (保持不变)
# ==========================================

st.markdown("---")

# 创建左右两栏布局
left_col, right_col = st.columns(2)

# 左侧栏：输入区域
with left_col:
    st.header("📤 输入区域")
    
    # PDF 文件上传
    uploaded_file = st.file_uploader("上传您的简历 (PDF 格式)", type=["pdf"])
    
    # 显示提取的简历文本
    resume_text = ""
    if uploaded_file is not None:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                resume_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        resume_text += text + "\n"
            
            if resume_text.strip():
                st.success(f"✅ 成功提取简历文本 ({len(resume_text)} 字符)")
            else:
                st.warning("⚠️ PDF 文件中未能提取到文本")
                
        except Exception as e:
            st.error(f"❌ PDF 处理出错: {str(e)}")
    
    # 职位描述输入框
    job_description = st.text_area(
        "输入职位描述 (JD)",
        height=250,
        placeholder="请粘贴目标职位的职位描述..."
    )
    
    # 开始修改按钮
    st.markdown("---")
    start_button = st.button("🚀 开始修改", type="primary", use_container_width=True)

# 右侧栏：输出区域
with right_col:
    st.header("📝 AI 修改建议")
    
    if start_button:
        # 验证所有输入
        if not api_key:
            st.error("❌ 请先在左侧侧边栏输入 Google API Key")
        elif not uploaded_file:
            st.error("❌ 请先上传简历 PDF")
        elif not job_description.strip():
            st.error("❌ 请输入职位描述")
        else:
            # 调用 AI
            try:
                with st.spinner("🤖 AI 正在思考中..."):
                    # 提示词
                    full_prompt = f"""你是一个资深招聘官。请分析简历和JD。
                    
                    【简历内容】
                    {resume_text}
                    
                    【职位描述】
                    {job_description}
                    
                    请输出：
                    1. 匹配度分析
                    2. 缺失技能
                    3. 优化后的工作经历
                    """

                    # 使用最稳的 gemini-pro
                    model = genai.GenerativeModel('gemini-pro')
                    response = model.generate_content(full_prompt)
                    
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"❌ 调用失败: {str(e)}")
                st.warning("请检查您的 API Key 是否正确，或者尝试更换一个 Key")
