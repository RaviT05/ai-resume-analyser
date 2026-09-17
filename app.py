import streamlit as st
import PyPDF2
from groq import Groq
from dotenv import load_dotenv
import os
import io
import re
from datetime import datetime

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- Page config ----------------
st.set_page_config(page_title="AI Resume Analyser", page_icon="🚀", layout="centered")

# ---------------- Session state ----------------
if "history" not in st.session_state:
    st.session_state.history = []  # keeps last few analyses this session

# ---------------- Header ----------------
st.title("🚀 AI Resume Analyser")
st.write("Upload your resume and get instant AI powered feedback!")
st.divider()

# ---------------- Input section ----------------
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("📄 Upload your Resume (PDF only)", type="pdf")

with col2:
    job_role = st.text_input("🎯 Job role you are applying for", placeholder="Ex: ML Engineer, Python Developer")

# Optional: paste a job description for a much more accurate ATS match
job_description = st.text_area(
    "📋 (Optional) Paste the job description for a more accurate ATS keyword match",
    placeholder="Paste the full job posting here for better keyword matching...",
    height=120,
)

st.divider()


# ---------------- Helper functions ----------------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file. Returns '' if nothing could be extracted."""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text.strip()


def extract_score(ai_text: str):
    """Pulls a number like '7/10' or '7 out of 10' out of the AI response."""
    match = re.search(r"(\d{1,2})\s*(?:/|out of)\s*10", ai_text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        return min(score, 10)
    return None


def score_verdict(score: int):
    if score is None:
        return "No score detected", "⚪"
    if score >= 8:
        return "Excellent resume!", "🟢"
    elif score >= 6:
        return "Good, but room to improve", "🟡"
    else:
        return "Needs significant work", "🔴"


def get_ats_keywords(role: str, description: str):
    """Build a keyword list from job description if given, otherwise fall back
    to a small built-in list based on the role name."""
    if description.strip():
        # crude but effective: pull significant words from the JD
        words = re.findall(r"[A-Za-z][A-Za-z\+\#\.]{2,}", description)
        stop_words = {
            "the", "and", "for", "with", "you", "are", "will", "our", "have",
            "this", "that", "your", "job", "role", "work", "team", "years",
            "experience", "skills", "ability", "strong", "excellent", "who",
            "from", "into", "able", "using", "must", "can", "any", "all",
        }
        keywords = sorted(set(w.lower() for w in words if w.lower() not in stop_words and len(w) > 2))
        return keywords[:40]  # cap to keep it manageable
    else:
        # fallback generic keyword bank by common role type
        base = {
            "python": ["python", "django", "flask", "pandas", "numpy", "api", "sql", "git"],
            "data": ["python", "sql", "excel", "pandas", "numpy", "visualization", "statistics", "machine learning"],
            "ml": ["python", "machine learning", "tensorflow", "pytorch", "scikit-learn", "numpy", "pandas", "deep learning"],
            "web": ["html", "css", "javascript", "react", "node", "api", "git", "responsive"],
            "java": ["java", "spring", "sql", "oop", "rest api", "git", "maven"],
        }
        role_lower = role.lower()
        for key, kw in base.items():
            if key in role_lower:
                return kw
        return ["communication", "teamwork", "problem solving", "git", "sql", "python"]


def calculate_ats_match(resume_text: str, keywords: list):
    resume_lower = resume_text.lower()
    matched = [kw for kw in keywords if kw.lower() in resume_lower]
    missing = [kw for kw in keywords if kw.lower() not in resume_lower]
    match_pct = round((len(matched) / len(keywords)) * 100) if keywords else 0
    return match_pct, matched, missing


# ---------------- Analyse button ----------------
if st.button("⚡ Analyse My Resume", use_container_width=True):
    if uploaded_file is None:
        st.warning("Please upload your resume first!")
    elif job_role == "":
        st.warning("Please enter the job role you are applying for!")
    else:
        # Read PDF
        try:
            text = extract_text_from_pdf(uploaded_file.read())
        except Exception as e:
            st.error(f"Couldn't read that PDF: {e}")
            st.stop()

        if not text:
            st.error("Couldn't extract any text from this PDF. It might be a scanned image — try a text-based PDF instead.")
            st.stop()

        with st.spinner("AI is analysing your resume... please wait ⏳"):
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
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
                ai_feedback = response.choices[0].message.content
            except Exception as e:
                st.error(f"AI analysis failed: {e}")
                st.stop()

        # Parse score + ATS match
        score = extract_score(ai_feedback)
        verdict, emoji = score_verdict(score)
        keywords = get_ats_keywords(job_role, job_description)
        match_pct, matched_kw, missing_kw = calculate_ats_match(text, keywords)

        # Save to session history
        st.session_state.history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "role": job_role,
            "score": score,
            "match_pct": match_pct,
        })

        st.success("Analysis complete! ✅")
        st.divider()

        # ---------------- Rating summary (always visible, not buried in tabs) ----------------
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            st.metric("Resume Score", f"{score}/10" if score is not None else "N/A")
            if score is not None:
                st.progress(score / 10)
            st.caption(f"{emoji} {verdict}")
        with rcol2:
            st.metric("ATS Keyword Match", f"{match_pct}%")
            st.progress(match_pct / 100)
            st.caption("🟢 70%+" if match_pct >= 70 else ("🟡 40-69%" if match_pct >= 40 else "🔴 Below 40%"))

        st.divider()

        # ---------------- Tabs ----------------
        tab1, tab2, tab3 = st.tabs(["🤖 AI Feedback", "🔑 ATS Keyword Match", "⬇️ Download Report"])

        with tab1:
            st.subheader("AI Feedback on your Resume")
            st.write(ai_feedback)

        with tab2:
            st.subheader("Keyword Match Breakdown")
            st.write(f"Matched **{len(matched_kw)}** out of **{len(keywords)}** relevant keywords.")
            mcol, ncol = st.columns(2)
            with mcol:
                st.markdown("**✅ Found in your resume**")
                if matched_kw:
                    st.write(", ".join(matched_kw))
                else:
                    st.write("None found — consider adding role-relevant keywords.")
            with ncol:
                st.markdown("**❌ Missing keywords**")
                if missing_kw:
                    st.write(", ".join(missing_kw))
                else:
                    st.write("Great — no major gaps!")
            if not job_description.strip():
                st.info("Tip: paste the actual job description above next time for a much more accurate match.")

        with tab3:
            st.subheader("Download Your Report")
            report_text = f"""AI RESUME ANALYSER REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Job Role: {job_role}

RESUME SCORE: {score}/10 ({verdict})
ATS KEYWORD MATCH: {match_pct}%

Matched Keywords: {", ".join(matched_kw) if matched_kw else "None"}
Missing Keywords: {", ".join(missing_kw) if missing_kw else "None"}

--- AI FEEDBACK ---
{ai_feedback}
"""
            st.download_button(
                label="📥 Download Full Report (.txt)",
                data=report_text,
                file_name=f"resume_analysis_{job_role.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ---------------- Session history ----------------
if st.session_state.history:
    st.divider()
    with st.expander(f"📊 This session's analyses ({len(st.session_state.history)})"):
        for i, h in enumerate(reversed(st.session_state.history), 1):
            st.write(f"{i}. **{h['role']}** — Score: {h['score']}/10, ATS Match: {h['match_pct']}% (at {h['time']})")

st.divider()
st.caption("Built with Python, Streamlit and Groq AI 🔥")