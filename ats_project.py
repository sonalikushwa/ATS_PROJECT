# Filename: ats_checker.py

import streamlit as st
import PyPDF2
import docx
import re
import json

from google import genai

# ====== CONFIGURATION ======
API_KEY = st.secrets["GEMINI_API_KEY"]  # Replace with your actual key
MODEL = "gemini-2.5-flash"  # or "gemini-2.0-flash" etc — choose based on availability

# Create Gemini client
client = genai.Client(api_key=API_KEY)

# ====== HELPER FUNCTIONS ======
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def read_resume(uploaded_file):
    fname = uploaded_file.name.lower()
    if fname.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif fname.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return ""

def ats_evaluate(resume_text, jd_text):
    prompt = f"""
You are an expert hiring consultant.  
Compare the resume and the job description below.

=== JOB DESCRIPTION ===
{jd_text}

=== RESUME ===
{resume_text}

Provide output in **strict JSON** format with keys:
- score  (integer 0–100)
- strengths  (list of strings)
- missing_skills  (list of strings)
- verdict  (one of: Shortlist / Consider / Not a Match)
- recommendations  (list of strings)
"""
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
    except Exception as e:
        return {"error": f"API request failed: {e}"}

    text = resp.text.strip()
    # Sometimes Gemini returns extra text; extract JSON
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        text = m.group(0)

    try:
        result = json.loads(text)
    except Exception as e:
        return {"error": f"Failed to parse JSON: {e}\nResponse: {text}"}

    return result

# ====== STREAMLIT UI ======
st.set_page_config(page_title="ATS Resume Checker", layout="centered")
st.title("📄 ATS Resume Checker")

uploaded = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf","docx"])
jd = st.text_area("Paste Job Description", height=200)

if uploaded and jd:
    if st.button("Analyze"):
        resume_text = read_resume(uploaded)
        if not resume_text:
            st.error("Could not read resume — unsupported file or extraction failed.")
        else:
            with st.spinner("Evaluating..."):
                result = ats_evaluate(resume_text, jd)
            if result.get("error"):
                st.error(result["error"])
            else:
                st.subheader("📊 ATS Match Score")
                score = result.get("score", 0)
                st.metric("Score", f"{score} / 100")
                st.progress(score / 100)

                st.subheader("💪 Strengths")
                for s in result.get("strengths", []):
                    st.write(f"- {s}")

                st.subheader("⚠️ Missing or Weak Skills")
                for m in result.get("missing_skills", []):
                    st.write(f"- {m}")

                st.subheader("🧾 Verdict")
                st.write(result.get("verdict", "N/A"))

                st.subheader("📈 Recommendations")
                for r in result.get("recommendations", []):
                    st.write(f"- {r}")
else:
    st.info("Upload a resume and paste the job description to begin.")
