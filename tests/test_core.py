"""Unit tests for the Resume Screening Agent."""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ---------------------------------------------------------------------------
# config tests
# ---------------------------------------------------------------------------
class TestScoringWeights:
    def test_default_weights_valid(self):
        from config import ScoringWeights
        w = ScoringWeights()
        w.validate()  # should not raise

    def test_invalid_weights_raise(self):
        from config import ScoringWeights
        w = ScoringWeights(embeddings=0.5, required_skills=0.5, preferred_skills=0.5, experience=0.5)
        with pytest.raises(ValueError):
            w.validate()

    def test_as_dict_keys(self):
        from config import ScoringWeights
        d = ScoringWeights().as_dict()
        assert "Embeddings (semantic)" in d
        assert "Required Skills" in d


# ---------------------------------------------------------------------------
# extraction tests
# ---------------------------------------------------------------------------
class TestExtraction:
    def test_extract_email(self):
        from extraction import extract_email
        assert extract_email("Contact me at alice@example.com for details") == "alice@example.com"
        assert extract_email("no email here") is None

    def test_extract_phone(self):
        from extraction import extract_phone
        assert extract_phone("Call +1-800-555-0199 anytime") is not None
        assert extract_phone("no phone") is None

    def test_extract_years_experience(self):
        from extraction import extract_years_experience
        assert extract_years_experience("I have 5 years of experience in Python.") == 5.0
        assert extract_years_experience("8+ years of relevant experience") == 8.0
        assert extract_years_experience("No experience mentioned") is None

    def test_detect_experience_level_by_years(self):
        from extraction import detect_experience_level
        assert detect_experience_level("", years=1) == "Entry"
        assert detect_experience_level("", years=3) == "Mid"
        assert detect_experience_level("", years=6) == "Senior"
        assert detect_experience_level("", years=10) == "Lead/Principal"

    def test_detect_experience_level_by_title(self):
        from extraction import detect_experience_level
        assert detect_experience_level("Senior Software Engineer") == "Senior"
        assert detect_experience_level("Junior Developer") == "Entry"
        assert detect_experience_level("Staff Engineer") == "Lead/Principal"

    def test_extract_skills(self):
        from extraction import extract_skills
        skills = extract_skills("Experienced in Python, AWS, Docker, and TensorFlow.")
        assert "Python" in skills
        assert "AWS" in skills
        assert "Docker" in skills
        assert "TensorFlow" in skills

    def test_extract_education(self):
        from extraction import extract_education
        edu = extract_education("Holds a B.S. in Computer Science and M.S. in AI.")
        assert len(edu) >= 1

    def test_extract_certifications(self):
        from extraction import extract_certifications
        certs = extract_certifications("Holds AWS Certified Solutions Architect and PMP certifications.")
        assert any("AWS Certified" in c for c in certs)
        assert "PMP" in certs


# ---------------------------------------------------------------------------
# scoring tests
# ---------------------------------------------------------------------------
class TestScoring:
    def test_get_recommendation(self):
        from scoring import get_recommendation
        assert "Strongly" in get_recommendation(80)
        assert "Consider" in get_recommendation(60)
        assert "Not Recommended" in get_recommendation(40)

    def test_experience_score_meets_requirement(self):
        from scoring import _experience_score
        score = _experience_score(years=5, jd_text="Requires 3 years of experience in Python.")
        assert score == 100.0

    def test_experience_score_below_requirement(self):
        from scoring import _experience_score
        score = _experience_score(years=1, jd_text="Requires 5 years of experience.")
        assert score < 100.0

    def test_experience_score_unknown(self):
        from scoring import _experience_score
        score = _experience_score(years=None, jd_text="Requires 5 years of experience.")
        assert score == 50.0

    def test_skill_scores(self):
        from scoring import _skill_scores
        req, pref, matched_req, matched_pref = _skill_scores(
            resume_skills=["Python", "Docker", "AWS"],
            jd_text="Looking for Python and Docker developer with AWS experience.",
        )
        assert req > 0
        assert len(matched_req) > 0


# ---------------------------------------------------------------------------
# utils tests
# ---------------------------------------------------------------------------
class TestUtils:
    def _sample_results(self):
        return [
            {
                "rank": 1, "name": "alice.pdf", "score": 85.0,
                "recommendation": "✅ Strongly Recommend",
                "email": "alice@example.com", "phone": "555-0100",
                "years_experience": 5, "experience_level": "Senior",
                "skills": ["Python", "AWS"], "education": ["B.S. CS"],
                "certifications": ["AWS Certified"],
                "embedding_score": 80.0, "required_score": 90.0,
                "preferred_score": 70.0, "experience_score": 100.0,
                "matched_required": ["Python"], "matched_preferred": ["AWS"],
                "explanation": "test", "analysis": "Strong candidate.",
            }
        ]

    def test_results_to_csv(self):
        from utils import results_to_csv
        csv = results_to_csv(self._sample_results())
        assert "alice.pdf" in csv
        assert "85.0" in csv

    def test_results_to_json(self):
        from utils import results_to_json
        import json
        data = json.loads(results_to_json(self._sample_results()))
        assert data[0]["name"] == "alice.pdf"

    def test_results_to_excel(self):
        from utils import results_to_excel
        xlsx = results_to_excel(self._sample_results())
        assert isinstance(xlsx, bytes)
        assert len(xlsx) > 0

    def test_build_export_df(self):
        from utils import build_export_df
        df = build_export_df(self._sample_results())
        assert "Candidate" in df.columns
        assert df.iloc[0]["Score (%)"] == 85.0
