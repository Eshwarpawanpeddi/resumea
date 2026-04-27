"""AI Resume Screening Agent – Enhanced Streamlit Application."""

import logging
import os

import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer

from config import Config, ScoringWeights
from extraction import parse_resume
from scoring import calculate_score, get_recommendation
from utils import (
    generate_llm_analysis,
    results_to_csv,
    results_to_excel,
    results_to_json,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Screening Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load config from environment
# ---------------------------------------------------------------------------
cfg = Config.from_env()


# ---------------------------------------------------------------------------
# Cached model loading
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading embedding model…")
def load_model(model_name: str):
    return SentenceTransformer(model_name)


# ---------------------------------------------------------------------------
# Sidebar – Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Settings")

    st.subheader("🤖 Embedding Model")
    embedding_model_name = st.selectbox(
        "Model",
        options=[
            "paraphrase-multilingual-mpnet-base-v2",
            "all-MiniLM-L6-v2",
            "all-mpnet-base-v2",
        ],
        index=0,
        help="paraphrase-multilingual-mpnet-base-v2 offers better semantic accuracy and multilingual support.",
    )

    st.subheader("🔑 LLM Integration (Optional)")
    llm_provider = st.selectbox(
        "LLM Provider",
        options=["None (Embeddings only)", "Google Gemini", "Anthropic Claude"],
        index=0,
        help="Select an LLM to generate detailed candidate analysis.",
    )

    google_api_key = cfg.google_api_key or ""
    anthropic_api_key = cfg.anthropic_api_key or ""

    if llm_provider == "Google Gemini":
        gemini_model = st.selectbox(
            "Gemini Model",
            ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        )
        google_api_key = st.text_input(
            "Google API Key",
            value=google_api_key,
            type="password",
            placeholder="AIza…",
            help="Get a free key at https://makersuite.google.com",
        )
        llm_provider_key = "gemini"
        llm_model_name = gemini_model
        llm_api_key = google_api_key
    elif llm_provider == "Anthropic Claude":
        anthropic_model = st.selectbox(
            "Claude Model",
            ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
        )
        anthropic_api_key = st.text_input(
            "Anthropic API Key",
            value=anthropic_api_key,
            type="password",
            placeholder="sk-ant-…",
        )
        llm_provider_key = "anthropic"
        llm_model_name = anthropic_model
        llm_api_key = anthropic_api_key
    else:
        llm_provider_key = "none"
        llm_model_name = ""
        llm_api_key = ""

    st.subheader("📊 Scoring Weights")
    st.caption("Weights must sum to 100%")
    weight_embeddings = st.slider("Embeddings (semantic)", 0, 100, 40)
    weight_required = st.slider("Required Skills", 0, 100, 35)
    weight_preferred = st.slider("Preferred Skills", 0, 100, 15)
    weight_experience = st.slider("Experience", 0, 100, 10)
    total_w = weight_embeddings + weight_required + weight_preferred + weight_experience
    if total_w != 100:
        st.warning(f"⚠️ Weights sum to {total_w}% (must be 100%)")
        weights_valid = False
    else:
        weights_valid = True

    weights = ScoringWeights(
        embeddings=weight_embeddings / 100,
        required_skills=weight_required / 100,
        preferred_skills=weight_preferred / 100,
        experience=weight_experience / 100,
    )

    st.subheader("🔧 Processing")
    max_pages = st.number_input("Max PDF pages", min_value=1, max_value=20, value=5)

    # Theme hint
    st.markdown("---")
    st.caption(
        "💡 Switch between light and dark mode via Streamlit's ☰ menu → Settings"
    )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <h1 style='text-align:center;'>📄 AI Resume Screening Agent</h1>
    <p style='text-align:center; color:grey;'>Semantic Matching · Skill Analysis · LLM-Enhanced Insights</p>
    <hr/>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Main layout: Job Description + Resume Upload
# ---------------------------------------------------------------------------
col_jd, col_up = st.columns([1, 1])

with col_jd:
    st.subheader("📋 Job Description")
    jd_text = st.text_area(
        "Paste job description here…",
        height=280,
        placeholder="Senior AI Engineer – Python, ML, AWS, Docker…",
    )

with col_up:
    st.subheader("📄 Upload Resumes (PDF)")
    files = st.file_uploader(
        "Select one or more PDF resumes",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if files:
        st.success(f"✅ {len(files)} file(s) selected")

# ---------------------------------------------------------------------------
# Screen Resumes button
# ---------------------------------------------------------------------------
screen_btn = st.button(
    "🚀 SCREEN RESUMES",
    type="primary",
    use_container_width=True,
    disabled=not weights_valid,
)

if screen_btn:
    # Validation
    if not jd_text.strip():
        st.error("❌ Please provide a job description.")
        st.stop()
    if not files:
        st.error("❌ Please upload at least one resume.")
        st.stop()

    model = load_model(embedding_model_name)

    progress_bar = st.progress(0, text="Loading…")
    status = st.empty()
    results: list[dict] = []

    for idx, file in enumerate(files):
        pct = (idx + 1) / len(files)
        status.info(f"🔍 Processing **{file.name}** ({idx+1}/{len(files)})…")
        progress_bar.progress(pct, text=f"Processing {idx+1}/{len(files)}")

        # 1. Extract resume data
        resume_data = parse_resume(file, max_pages=int(max_pages))

        # 2. Score
        score_data = calculate_score(resume_data, jd_text, model, weights)

        # 3. LLM analysis
        with st.spinner(f"Generating analysis for {file.name}…"):
            analysis = generate_llm_analysis(
                candidate_name=file.name,
                resume_data=resume_data,
                jd_text=jd_text,
                score_data=score_data,
                provider=llm_provider_key,
                api_key=llm_api_key if llm_api_key else None,
                model_name=llm_model_name,
            )

        results.append(
            {
                "rank": 0,  # filled after sorting
                "name": file.name,
                "score": score_data["score"],
                "recommendation": get_recommendation(score_data["score"]),
                "email": resume_data.get("email"),
                "phone": resume_data.get("phone"),
                "years_experience": resume_data.get("years_experience"),
                "experience_level": resume_data.get("experience_level"),
                "skills": resume_data.get("skills", []),
                "education": resume_data.get("education", []),
                "certifications": resume_data.get("certifications", []),
                "embedding_score": score_data["embedding_score"],
                "required_score": score_data["required_score"],
                "preferred_score": score_data["preferred_score"],
                "experience_score": score_data["experience_score"],
                "matched_required": score_data["matched_required"],
                "matched_preferred": score_data["matched_preferred"],
                "explanation": score_data["explanation"],
                "analysis": analysis,
            }
        )

    # Sort by score and assign ranks
    results.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    progress_bar.empty()
    status.success(f"✅ Screening complete! {len(results)} candidate(s) processed.")

    # Store in session state so the dashboard persists
    st.session_state["results"] = results
    st.session_state["jd_text"] = jd_text

# ---------------------------------------------------------------------------
# Results Dashboard
# ---------------------------------------------------------------------------
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]

    st.markdown("---")
    st.header("🏆 Ranked Candidates")

    # --- Analytics row ---
    scores = [r["score"] for r in results]
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Candidates", len(results))
    a2.metric("Average Score", f"{np.mean(scores):.1f}%")
    a3.metric("Top Score", f"{max(scores):.1f}%")
    strongly = sum(1 for r in results if r["score"] >= 75)
    a4.metric("Strongly Recommended", strongly)

    # --- Filter & sort ---
    with st.expander("🔍 Filter & Sort Options", expanded=False):
        fc1, fc2 = st.columns(2)
        min_score = fc1.slider("Minimum score (%)", 0, 100, 0)
        level_filter = fc2.multiselect(
            "Experience level",
            ["Entry", "Mid", "Senior", "Lead/Principal"],
            default=["Entry", "Mid", "Senior", "Lead/Principal"],
        )

    filtered = [
        r for r in results
        if r["score"] >= min_score and r["experience_level"] in level_filter
    ]

    # --- Summary table ---
    table_data = []
    for r in filtered:
        table_data.append(
            {
                "Rank": r["rank"],
                "Candidate": r["name"],
                "Score": f"{r['score']}%",
                "Recommendation": r["recommendation"],
                "Experience Level": r["experience_level"] or "—",
                "Years Exp.": r["years_experience"] or "—",
                "Skills Found": len(r["skills"]),
                "Email": r["email"] or "—",
            }
        )
    if table_data:
        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No candidates match the current filter criteria.")

    # --- Detailed profiles ---
    st.markdown("---")
    st.header("👤 Candidate Profiles")

    for r in filtered:
        with st.expander(
            f"#{r['rank']} — {r['name']}  |  Score: {r['score']}%  |  {r['recommendation']}",
            expanded=(r["rank"] == 1),
        ):
            p1, p2, p3 = st.columns(3)

            p1.markdown("**📊 Score Breakdown**")
            p1.progress(int(r["embedding_score"]), text=f"Semantic: {r['embedding_score']}%")
            p1.progress(int(r["required_score"]), text=f"Required Skills: {r['required_score']}%")
            p1.progress(int(r["preferred_score"]), text=f"Preferred Skills: {r['preferred_score']}%")
            p1.progress(int(r["experience_score"]), text=f"Experience: {r['experience_score']}%")

            p2.markdown("**🧑 Candidate Info**")
            p2.write(f"📧 **Email:** {r['email'] or '—'}")
            p2.write(f"📱 **Phone:** {r['phone'] or '—'}")
            p2.write(f"🏆 **Level:** {r['experience_level'] or '—'}")
            p2.write(f"📅 **Years Exp:** {r['years_experience'] or '—'}")
            if r["education"]:
                p2.write("🎓 **Education:**")
                for edu in r["education"][:3]:
                    p2.write(f"  • {edu}")
            if r["certifications"]:
                p2.write(f"📜 **Certs:** {', '.join(r['certifications'][:5])}")

            p3.markdown("**🛠️ Skills & Analysis**")
            if r["matched_required"]:
                p3.write(f"✅ **Matched Required:** {', '.join(r['matched_required'][:8])}")
            if r["matched_preferred"]:
                p3.write(f"⭐ **Matched Preferred:** {', '.join(r['matched_preferred'][:6])}")
            if r["skills"]:
                p3.write(f"🔧 **All Skills:** {', '.join(r['skills'][:15])}")

            if r.get("analysis"):
                st.markdown("**🤖 Analysis**")
                st.markdown(r["analysis"])

            st.caption(f"*Score explanation: {r['explanation']}*")

    # --- Comparison (top 3) ---
    if len(filtered) >= 2:
        st.markdown("---")
        st.header("⚖️ Top Candidates Comparison")
        top3 = filtered[:3]
        comp_cols = st.columns(len(top3))
        for col, r in zip(comp_cols, top3):
            col.markdown(f"**#{r['rank']} {r['name']}**")
            col.metric("Score", f"{r['score']}%")
            col.write(f"**Level:** {r['experience_level'] or '—'}")
            col.write(f"**Skills:** {len(r['skills'])}")
            col.write(f"**Matched Required:** {len(r['matched_required'])}")
            col.write(r["recommendation"])

    # --- Export ---
    st.markdown("---")
    st.header("📥 Export Results")
    ex1, ex2, ex3 = st.columns(3)

    csv_data = results_to_csv(results)
    ex1.download_button(
        "📊 Download CSV",
        data=csv_data,
        file_name="screening_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

    json_data = results_to_json(results)
    ex2.download_button(
        "📋 Download JSON",
        data=json_data,
        file_name="screening_results.json",
        mime="application/json",
        use_container_width=True,
    )

    try:
        excel_data = results_to_excel(results)
        ex3.download_button(
            "📗 Download Excel",
            data=excel_data,
            file_name="screening_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except ImportError:
        ex3.info("Install openpyxl for Excel export.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; color:grey; font-size:0.85em;'>
    <b>AI Resume Screening Agent</b> &nbsp;|&nbsp;
    Semantic Matching · Multi-factor Scoring · LLM Analysis<br/>
    <em>Model: paraphrase-multilingual-mpnet-base-v2 &nbsp;|&nbsp;
    Framework: Streamlit · Sentence Transformers · scikit-learn</em>
    </div>
    """,
    unsafe_allow_html=True,
)
