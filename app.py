import streamlit as st
import PyPDF2
from groq import Groq
from dotenv import load_dotenv
import os
import io

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Page config
st.set_page_config(page_title="AI Resume Analyser", page_icon="🚀")

# Header
st.title("🚀 AI Resume Analyser")
st.write("Upload your resume and get instant AI powered feedback!")
st.divider()

# Input section
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("📄 Upload your Resume (PDF only)", type="pdf")

with col2:
    job_role = st.text_input("🎯 Job role you are applying for", placeholder="Ex: ML Engineer, Python Developer")

st.divider()

# Analyse button
if st.button("⚡ Analyse My Resume", use_container_width=True):
    if uploaded_file is None:
        st.warning("Please upload your resume first!")
    elif job_role == "":
        st.warning("Please enter the job role you are applying for!")
    else:
        # Read PDF
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        with st.spinner("AI is analysing your resume... please wait ⏳"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyse this resume for the role of {job_role} and give feedback in this exact format:

1. STRENGTHS (3 points)
2. WEAKNESSES (3 points)
3. SKILL GAPS (skills missing for {job_role})
4. OVERALL SCORE (out of 10)
5. ONE TIP TO IMPROVE

Resume text:
{text}"""
                    }
                ]
            )

        st.success("Analysis complete! ✅")
        st.divider()
        st.subheader("🤖 AI Feedback on your Resume")
        st.write(response.choices[0].message.content)

st.divider()
st.caption("Built with Python, Streamlit and Groq AI 🔥")