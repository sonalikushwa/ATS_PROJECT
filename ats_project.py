import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="ATS Resume Checker", layout="wide")
st.title("📄 AI Powered ATS Resume Checker")

# ---------------- API KEY (NO INPUT REQUIRED) ----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = "gemini-2.5-flash"

# ---------------- RESUME UPLOAD ----------------
uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])


# ---------------- HELPER FUNCTIONS ----------------
def extract_text_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        try:
            t = page.extract_text()
            if t:
                text += t + "\n"
        except:
            pass
    return text


def extract_text_docx(file):
    doc = docx.Document(file)
    return "\n".join(par.text for par in doc.paragraphs)


def generate_ats_score(resume_text):
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    You are an ATS scoring AI. Evaluate the resume and return only:

    ATS Score: X/100

    Resume:
    {resume_text}
    """

    response = model.generate_content(prompt)
    return response.text


def generate_full_analysis(resume_text):
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    You are an ATS evaluation AI. Analyze the resume and return:

    Strengths:
    - ...

    Weaknesses:
    - ...

    Missing Keywords:
    - ...

    Suggestions:
    - ...

    Suitable Job Roles:
    - ...

    Resume:
    {resume_text}
    """

    response = model.generate_content(prompt)
    return response.text


# ---------------- MAIN PROCESS ----------------
if uploaded_file:

    # Extract resume text
    if uploaded_file.name.endswith(".pdf"):
        resume_text = extract_text_pdf(uploaded_file)
    else:
        resume_text = extract_text_docx(uploaded_file)

    # ATS SCORE SECTION
    st.subheader("🔹 ATS Score")
    with st.spinner("Calculating ATS score..."):
        ats_result = generate_ats_score(resume_text)

    score_match = re.search(r"ATS Score:\s*(\d+)", ats_result)
    ats_score = int(score_match.group(1)) if score_match else 0

    st.progress(ats_score / 100)
    st.write(f"### ⭐ Your ATS Score: **{ats_score}/100**")

    # FULL ANALYSIS SECTION
    st.subheader("🔹 Full Resume Analysis")
    if st.button("Show Full Analysis"):
        with st.spinner("Generating detailed analysis..."):
            full_result = generate_full_analysis(resume_text)
        st.write(full_result)

else:
    st.info("Upload your resume to continue.")



