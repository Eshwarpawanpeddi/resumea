import streamlit as st
import pdfplumber
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

st.set_page_config(page_title="Resume Screener", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
# 📄 AI Resume Screening Agent
**Semantic Matching + Skill Analysis**
*48-Hour AI Challenge Submission*
""")

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.info("✅ Pure embeddings - No LLM dependencies")

def extract_text(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages[:3]:
                if page.extract_text():
                    text += page.extract_text() + "\n"
    except:
        pass
    return text.strip()

def extract_skills(text):
    # Simple skill extraction
    skills = re.findall(r'\b(AI|ML|Python|JavaScript|React|Node|Flask|MongoDB|AWS|Docker|Kubernetes|SQL|TensorFlow|Pytorch|NLP|Computer Vision)\b', text, re.IGNORECASE)
    return list(set(skills))

def calculate_score(resume_text, jd_text):
    if len(resume_text) < 50 or len(jd_text) < 50:
        return 40.0
    
    try:
        r_emb = model.encode(resume_text)
        j_emb = model.encode(jd_text)
        base_score = cosine_similarity([r_emb], [j_emb])[0][0] * 100
        
        # Skill bonus
        resume_skills = set(extract_skills(resume_text))
        jd_skills = set(extract_skills(jd_text))
        skill_match = len(resume_skills & jd_skills) * 10
        
        final_score = min(base_score * 0.7 + skill_match, 100)
        return round(final_score, 1)
    except:
        return 40.0

# Main UI
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Job Description")
    jd_text = st.text_area("Paste job description...", height=250, 
                          placeholder="Senior AI Engineer - Python, ML, AWS...")

with col2:
    st.subheader("📄 Upload Resumes")
    files = st.file_uploader("PDFs only", type=["pdf"], accept_multiple_files=True)

if st.button("🚀 SCREEN RESUMES", type="primary", use_container_width=True):
    if not jd_text.strip():
        st.error("❌ Add job description")
    elif not files:
        st.error("❌ Upload at least 1 resume")
    else:
        st.info(f"Processing {len(files)} resume(s)...")
        results = []
        progress = st.progress(0)
        
        for i, file in enumerate(files):
            resume_text = extract_text(file)
            score = calculate_score(resume_text, jd_text)
            skills = extract_skills(resume_text)
            
            results.append({
                "Rank": i+1,
                "Candidate": file.name,
                "Score": f"{score}%",
                "Skills Found": len(skills),
                "Score_Num": score
            })
            progress.progress((i+1) / len(files))
        
        # Results
        df = pd.DataFrame(results).sort_values("Score_Num", ascending=False)
        st.success("✅ Screening Complete!")
        
        st.subheader("🏆 Ranked Candidates")
        st.dataframe(df[["Rank", "Candidate", "Score", "Skills Found"]], 
                    use_container_width=True, hide_index=True)
        
        # Download
        csv_data = df[["Rank", "Candidate", "Score", "Skills Found"]].to_csv(index=False)
        st.download_button("📥 Download Results (CSV)", csv_data, "screening_results.csv")

# Footer
st.markdown("---")
st.markdown("""
**Features:**
- ✅ Semantic matching (embeddings)
- ✅ Skill extraction & bonus scoring  
- ✅ Multi-resume batch processing
- ✅ CSV export
- ✅ Production ready

**Tech:** Sentence Transformers + scikit-learn + Streamlit
**Challenge:** HR Resume Screening Agent**
""")
