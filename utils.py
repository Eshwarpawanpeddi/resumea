"""Utility helpers: LLM analysis, export, and formatting."""

import json
import logging
from io import BytesIO
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM Analysis
# ---------------------------------------------------------------------------

def _call_gemini(api_key: str, model_name: str, prompt: str) -> str:
    """Call Google Gemini API and return the text response."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini API error: %s", exc)
        return ""


def _call_anthropic(api_key: str, model_name: str, prompt: str) -> str:
    """Call Anthropic Claude API and return the text response."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as exc:
        logger.warning("Anthropic API error: %s", exc)
        return ""


def generate_llm_analysis(
    candidate_name: str,
    resume_data: dict,
    jd_text: str,
    score_data: dict,
    provider: str = "none",
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.0-flash",
) -> str:
    """
    Use an LLM to generate a detailed hiring recommendation for a candidate.
    Falls back to a rule-based summary if no LLM is configured.
    """
    prompt = f"""You are an expert HR recruiter. Analyze the following resume against the job description and provide a concise hiring recommendation.

Job Description:
{jd_text[:1500]}

Candidate: {candidate_name}
Match Score: {score_data.get("score", 0)}%
Skills Found: {", ".join(resume_data.get("skills", [])[:20]) or "None detected"}
Years of Experience: {resume_data.get("years_experience") or "Unknown"}
Experience Level: {resume_data.get("experience_level", "Unknown")}
Education: {"; ".join(resume_data.get("education", [])) or "Not listed"}
Certifications: {", ".join(resume_data.get("certifications", [])) or "None listed"}
Score Breakdown: {score_data.get("explanation", "")}

Please provide:
1. Top 3 strengths of this candidate
2. Key gaps or concerns
3. Final recommendation (Strongly Recommend / Consider / Not Recommended) with 1-sentence justification

Keep the response concise (under 200 words).
"""

    text = ""
    if provider == "gemini" and api_key:
        text = _call_gemini(api_key, model_name, prompt)
    elif provider == "anthropic" and api_key:
        text = _call_anthropic(api_key, model_name, prompt)

    if not text:
        # Rule-based fallback
        score = score_data.get("score", 0)
        matched = score_data.get("matched_required", [])
        text = (
            f"**Score:** {score}%\n"
            f"**Matched skills:** {', '.join(matched[:8]) or 'None detected'}\n"
            f"**Experience level:** {resume_data.get('experience_level', 'Unknown')}\n"
            f"**Recommendation:** {_recommendation_text(score)}"
        )
    return text


def _recommendation_text(score: float) -> str:
    if score >= 75:
        return "Strongly Recommend – candidate meets or exceeds requirements."
    if score >= 55:
        return "Consider for Interview – partial match; further evaluation advised."
    return "Not Recommended – significant skill or experience gaps identified."


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def build_export_df(results: list[dict]) -> pd.DataFrame:
    """Convert the list of result dicts to a clean export DataFrame."""
    rows = []
    for r in results:
        rows.append({
            "Rank": r.get("rank"),
            "Candidate": r.get("name"),
            "Score (%)": r.get("score"),
            "Recommendation": r.get("recommendation"),
            "Email": r.get("email") or "",
            "Phone": r.get("phone") or "",
            "Experience (yrs)": r.get("years_experience") or "",
            "Experience Level": r.get("experience_level", ""),
            "Skills Found": len(r.get("skills", [])),
            "Skills List": ", ".join(r.get("skills", [])[:20]),
            "Education": "; ".join(r.get("education", [])),
            "Certifications": ", ".join(r.get("certifications", [])),
            "Embedding Score": r.get("embedding_score"),
            "Required Skills Score": r.get("required_score"),
            "Preferred Skills Score": r.get("preferred_score"),
            "Experience Score": r.get("experience_score"),
            "LLM Analysis": r.get("analysis", ""),
        })
    return pd.DataFrame(rows)


def results_to_csv(results: list[dict]) -> str:
    """Return CSV string from results list."""
    return build_export_df(results).to_csv(index=False)


def results_to_json(results: list[dict]) -> str:
    """Return JSON string from results list."""
    return json.dumps(results, indent=2, default=str)


def results_to_excel(results: list[dict]) -> bytes:
    """Return Excel file bytes from results list."""
    df = build_export_df(results)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Screening Results")
        ws = writer.sheets["Screening Results"]
        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)
    return buf.getvalue()
