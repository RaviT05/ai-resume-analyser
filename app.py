import streamlit as st
import PyPDF2
from groq import Groq
from dotenv import load_dotenv
import os
import io

# Load environment variables
load_dotenv()

# Configure Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.title("AI Resume Analyser 🚀")
st.write("Upload your resume and get AI powered feedback!")

uploaded_file = st.file_uploader("Upload your Resume (PDF only)", type="pdf")

if uploaded_file is not None:
    st.success("Resume uploaded successfully! ✅")

    # Read the PDF
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))

    # Extract text from all pages
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    st.subheader("Analysing your resume... please wait ⏳")

    # Send to Groq AI
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""Analyse this resume and give feedback in this exact format:

1. STRENGTHS (3 points)
2. WEAKNESSES (3 points)
3. SKILL GAPS (what skills are missing)
4. OVERALL SCORE (out of 10)
5. ONE TIP TO IMPROVE

Resume text:
{text}"""
            }
        ]
    )

    st.subheader("AI Feedback on your Resume 🤖")
    st.write(response.choices[0].message.content)

else:
    st.info("Please upload your resume PDF above.")