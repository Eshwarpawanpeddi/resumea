"""Advanced multi-factor scoring system for resume–job description matching."""

import logging
import re
from typing import Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config import ScoringWeights
from extraction import extract_skills

logger = logging.getLogger(__name__)


def _embedding_score(resume_text: str, jd_text: str, model) -> float:
    """Cosine-similarity score between the two embeddings (0–100)."""
    try:
        r_emb = model.encode(resume_text)
        j_emb = model.encode(jd_text)
        sim = cosine_similarity([r_emb], [j_emb])[0][0]
        return float(np.clip(sim * 100, 0, 100))
    except Exception as exc:
        logger.warning("Embedding score error: %s", exc)
        return 40.0


def _skill_scores(
    resume_skills: list[str],
    jd_text: str,
    required_patterns: Optional[list[str]] = None,
    preferred_patterns: Optional[list[str]] = None,
) -> tuple[float, float, list[str], list[str]]:
    """
    Return (required_score 0-100, preferred_score 0-100, matched_required, matched_preferred).
    Skills are extracted from JD if explicit lists are not provided.
    """
    jd_skills = extract_skills(jd_text)
    resume_skill_lower = {s.lower() for s in resume_skills}

    # Split JD skills into required / preferred heuristically
    if not required_patterns:
        # Treat top 60% as required, rest preferred
        split = max(1, int(len(jd_skills) * 0.6))
        required_patterns = jd_skills[:split]
        preferred_patterns = jd_skills[split:]

    def match(skill_list):
        matched = []
        for skill in skill_list:
            if skill.lower() in resume_skill_lower:
                matched.append(skill)
        return matched

    matched_req = match(required_patterns)
    matched_pref = match(preferred_patterns)

    req_score = (len(matched_req) / max(len(required_patterns), 1)) * 100
    pref_score = (len(matched_pref) / max(len(preferred_patterns), 1)) * 100

    return req_score, pref_score, matched_req, matched_pref


def _experience_score(years: Optional[float], jd_text: str) -> float:
    """Score experience level match (0–100)."""
    # Try to detect required experience from JD
    patterns = [
        r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:relevant\s+)?experience",
        r"(\d+)\+?\s*yrs?\s+(?:of\s+)?experience",
        r"minimum\s+(?:of\s+)?(\d+)\s+years?",
        r"at\s+least\s+(\d+)\s+years?",
    ]
    required_years = None
    for p in patterns:
        m = re.search(p, jd_text, re.IGNORECASE)
        if m:
            required_years = float(m.group(1))
            break

    if years is None:
        return 50.0  # neutral if unknown

    if required_years is None:
        # Score based on absolute experience
        return float(np.clip(years / 10 * 100, 0, 100))

    if years >= required_years:
        return 100.0
    ratio = years / required_years
    return float(np.clip(ratio * 100, 0, 100))


def calculate_score(
    resume_data: dict,
    jd_text: str,
    model,
    weights: Optional[ScoringWeights] = None,
) -> dict:
    """
    Calculate a weighted multi-factor score for a single resume against a JD.

    Returns a dict with:
        score (float, 0-100), embedding_score, required_score, preferred_score,
        experience_score, matched_required, matched_preferred, explanation
    """
    if weights is None:
        weights = ScoringWeights()

    resume_text = resume_data.get("text", "")
    resume_skills = resume_data.get("skills", [])
    years_exp = resume_data.get("years_experience")

    # Fallback for very short texts
    if len(resume_text) < 50 or len(jd_text) < 50:
        return {
            "score": 40.0,
            "embedding_score": 40.0,
            "required_score": 0.0,
            "preferred_score": 0.0,
            "experience_score": 50.0,
            "matched_required": [],
            "matched_preferred": [],
            "explanation": "Insufficient text for analysis.",
        }

    emb_score = _embedding_score(resume_text, jd_text, model)
    req_score, pref_score, matched_req, matched_pref = _skill_scores(
        resume_skills, jd_text
    )
    exp_score = _experience_score(years_exp, jd_text)

    final = (
        emb_score * weights.embeddings
        + req_score * weights.required_skills
        + pref_score * weights.preferred_skills
        + exp_score * weights.experience
    )
    final = round(float(np.clip(final, 0, 100)), 1)

    # Build a human-readable explanation
    parts = []
    parts.append(f"Semantic match: {emb_score:.0f}/100 (weight {weights.embeddings*100:.0f}%)")
    parts.append(f"Required skills: {req_score:.0f}/100 (weight {weights.required_skills*100:.0f}%)")
    parts.append(f"Preferred skills: {pref_score:.0f}/100 (weight {weights.preferred_skills*100:.0f}%)")
    parts.append(f"Experience: {exp_score:.0f}/100 (weight {weights.experience*100:.0f}%)")
    explanation = " | ".join(parts)

    return {
        "score": final,
        "embedding_score": round(emb_score, 1),
        "required_score": round(req_score, 1),
        "preferred_score": round(pref_score, 1),
        "experience_score": round(exp_score, 1),
        "matched_required": matched_req,
        "matched_preferred": matched_pref,
        "explanation": explanation,
    }


def get_recommendation(score: float) -> str:
    """Convert a numeric score to a hiring recommendation label."""
    if score >= 75:
        return "✅ Strongly Recommend"
    if score >= 55:
        return "⚠️ Consider for Interview"
    return "❌ Not Recommended"
