import streamlit as st
import pdfplumber
import os
# 1. 改用 Google 官方库，不再用 openai
import google.generativeai as genai

# 页面配置
st.set_page_config(
    page_title="简历修改工具",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI 简历修改工具")
st.markdown("---")

# 2. 配置 Google API
# 依然使用环境变量，Streamlit Secrets 里名字必须是 GOOGLE_API_KEY
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 创建左右两栏布局
left_col, right_col = st.columns(2)

# 左侧栏：输入区域
with left_col:
    st.header("📤 输入区域")
    
    # PDF 文件上传
    uploaded_file = st.file_uploader(
        "上传您的简历 (PDF 格式)",
        type=["pdf"],
        help="请上传您的简历 PDF 文件"
    )
    
    # 显示提取的简历文本
    resume_text = ""
    if uploaded_file is not None:
        try:
            # 使用 pdfplumber 提取 PDF 文本
            with pdfplumber.open(uploaded_file) as pdf:
                resume_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        resume_text += text + "\n"
            
            if resume_text.strip():
                st.success(f"✅ 成功提取简历文本 ({len(resume_text)} 字符)")
                with st.expander("查看提取的简历内容"):
                    st.text_area(
                        "简历文本",
                        resume_text,
                        height=200,
                        disabled=True
                    )
            else:
                st.warning("⚠️ PDF 文件中未能提取到文本，请确保 PDF 不是扫描件")
                
        except Exception as e:
            st.error(f"❌ 处理 PDF 文件时出错: {str(e)}")
    else:
        st.info("👆 请上传您的简历 PDF 文件")
    
    # 职位描述输入框
    st.markdown("---")
    job_description = st.text_area(
        "输入职位描述 (JD)",
        height=250,
        placeholder="请粘贴目标职位的职位描述...\n\n例如：\n- 职位要求\n- 技术栈\n- 工作职责\n- 任职资格等"
    )
    
    # 开始修改按钮
    st.markdown("---")
    start_button = st.button(
        "🚀 开始修改",
        type="primary",
        use_container_width=True
    )

# 右侧栏：输出区域
with right_col:
    st.header("📝 AI 修改建议")
    
    # 检查是否点击了开始修改按钮
    if start_button:
        # 验证输入
        if not uploaded_file:
            st.error("❌ 请先上传简历 PDF 文件")
        elif not resume_text.strip():
            st.error("❌ 未能从 PDF 中提取到有效文本")
        elif not job_description.strip():
            st.error("❌ 请输入职位描述 (JD)")
        elif not api_key:
            st.error("❌ 未检测到 API Key，请在 Streamlit Secrets 中配置 GOOGLE_API_KEY")
        else:
            # 调用 Google Gemini API
            try:
                with st.spinner("🤖 AI 正在分析您的简历..."):
                    # System Prompt
                    system_prompt = """你是一个资深招聘官。请对比用户的简历和JD，找出简历中缺失的关键技能，并重写简历的工作经历部分，使其更符合JD要求。

请按照以下格式输出（使用 Markdown 格式）：

## 📊 匹配度分析
- 简要分析简历与JD的匹配情况

## ⚠️ 缺失的关键技能
- 列出简历中缺失但JD要求的关键技能

## ✍️ 工作经历优化建议
- 重写或优化工作经历部分，使其更符合JD要求
- 突出相关经验和成果
- 使用量化数据增强说服力

## 💡 其他建议
- 提供其他优化建议"""

                    # 3. 核心修改：Google SDK 喜欢把 System Prompt 和 用户内容拼在一起
                    full_prompt = f"{system_prompt}\n\n【用户简历】\n{resume_text}\n\n【职位描述】\n{job_description}"

                    # 初始化模型 (官方名字，不需要 base_url)
                    model = genai.GenerativeModel('gemini-pro')
                    
                    # 生成内容
                    response = model.generate_content(full_prompt)
                    
                    # 获取 AI 响应
                    ai_suggestion = response.text
                    
                    # 显示 AI 建议
                    st.markdown(ai_suggestion)
                    
            except Exception as e:
                st.error(f"❌ 调用 AI API 时出错: {str(e)}")
                st.info("💡 请检查您的 Secrets 配置是否正确")
    else:
        # 初始提示
        st.info("👈 请在左侧上传简历、输入职位描述，然后点击「开始修改」按钮")
        
        # 显示使用说明
        st.markdown("""
        ### 📖 使用说明
        
        1. **上传简历**: 上传您的简历 PDF 文件
        2. **输入 JD**: 粘贴目标职位的职位描述
        3. **开始修改**: 点击按钮，AI 将分析并给出修改建议
        """)

# 页脚
st.markdown("---")
st.caption("💡 提示：确保上传的 PDF 文件包含可提取的文本（非扫描件）")
