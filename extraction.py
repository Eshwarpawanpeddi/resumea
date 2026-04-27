"""Enhanced resume extraction module."""

import re
import logging
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Expanded skill database
# ---------------------------------------------------------------------------
SKILL_CATEGORIES = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl", "Shell",
        "Bash", "PowerShell", "SQL", "PL/SQL", "COBOL", "Fortran", "Haskell",
    ],
    "AI / ML": [
        "Machine Learning", "Deep Learning", "NLP", "Natural Language Processing",
        "Computer Vision", "Reinforcement Learning", "Neural Networks", "LLM",
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM",
        "Hugging Face", "Transformers", "BERT", "GPT", "RAG", "LangChain",
        "OpenAI", "Gemini", "Claude", "Stable Diffusion", "YOLO",
    ],
    "Data Engineering": [
        "Spark", "Hadoop", "Kafka", "Airflow", "dbt", "ETL", "Data Pipeline",
        "Databricks", "Snowflake", "BigQuery", "Redshift", "Hive", "Flink",
    ],
    "Databases": [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "DynamoDB", "SQLite", "Oracle", "MSSQL", "Neo4j", "InfluxDB",
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform",
        "Ansible", "Jenkins", "GitHub Actions", "CircleCI", "ArgoCD", "Helm",
        "CloudFormation", "Pulumi", "Prometheus", "Grafana", "EKS", "ECS",
    ],
    "Web & APIs": [
        "React", "Vue", "Angular", "Node.js", "Express", "FastAPI", "Flask",
        "Django", "REST", "GraphQL", "gRPC", "WebSocket", "Next.js", "Nuxt",
        "Spring Boot", "Microservices", "HTML", "CSS", "Tailwind",
    ],
    "Data Science": [
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Jupyter",
        "Statistics", "Data Analysis", "Data Visualization", "A/B Testing",
        "Feature Engineering", "Model Deployment", "MLflow", "Weights & Biases",
    ],
    "Other": [
        "Git", "Linux", "Agile", "Scrum", "Jira", "Confluence", "CI/CD",
        "Microservices", "System Design", "API Design", "Testing", "TDD",
    ],
}

ALL_SKILLS: list[str] = [
    skill for skills in SKILL_CATEGORIES.values() for skill in skills
]


def extract_text(pdf_file, max_pages: int = 5) -> str:
    """Extract text from a PDF file object, returning up to *max_pages* pages."""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages[:max_pages]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as exc:
        logger.warning("PDF extraction error: %s", exc)
    return text.strip()


def extract_email(text: str) -> Optional[str]:
    """Return the first email address found in *text*, or None."""
    pattern = r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Return the first phone-like string found in *text*, or None."""
    pattern = r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]"
    match = re.search(pattern, text)
    return match.group().strip() if match else None


def extract_years_experience(text: str) -> Optional[float]:
    """Detect total years of experience mentioned in the text."""
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+(?:of\s+)?(?:relevant\s+|work\s+)?experience",
        r"experience\s+of\s+(\d+(?:\.\d+)?)\+?\s*years?",
        r"(\d+(?:\.\d+)?)\+?\s*yrs?\s+(?:of\s+)?experience",
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+in\s+the\s+(?:field|industry)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def detect_experience_level(text: str, years: Optional[float] = None) -> str:
    """Return 'Entry', 'Mid', 'Senior', or 'Lead/Principal'."""
    text_lower = text.lower()

    # Explicit title signals
    if any(kw in text_lower for kw in ["staff engineer", "principal", "vp of", "director of"]):
        return "Lead/Principal"
    if any(kw in text_lower for kw in ["senior", "lead", "sr.", "sr "]):
        return "Senior"
    if any(kw in text_lower for kw in ["junior", "jr.", "jr ", "entry", "associate", "intern"]):
        return "Entry"

    # Fall back to years-of-experience
    if years is not None:
        if years >= 8:
            return "Lead/Principal"
        if years >= 4:
            return "Senior"
        if years >= 2:
            return "Mid"
        return "Entry"
    return "Mid"


def extract_skills(text: str) -> list[str]:
    """Return a deduplicated list of recognised skills found in *text*."""
    found = set()
    for skill in ALL_SKILLS:
        # Word-boundary match, case-insensitive
        pattern = r"(?<![A-Za-z])" + re.escape(skill) + r"(?![A-Za-z])"
        if re.search(pattern, text, re.IGNORECASE):
            found.add(skill)
    return sorted(found)


def extract_education(text: str) -> list[str]:
    """Extract degree / education-related phrases from *text*."""
    degrees = []
    patterns = [
        r"\b(Ph\.?D\.?|Doctor(?:ate)?)\b[^,\n]*",
        r"\b(M\.?S\.?|M\.?Sc\.?|Master(?:'s)?)\b[^,\n]*",
        r"\b(M\.?B\.?A\.?)\b[^,\n]*",
        r"\b(B\.?S\.?|B\.?E\.?|B\.?Tech\.?|Bachelor(?:'s)?)\b[^,\n]*",
        r"\b(Associate(?:'s)?)\b[^,\n]*",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            phrase = match.group().strip()[:80]
            if phrase not in degrees:
                degrees.append(phrase)
    return degrees


def extract_certifications(text: str) -> list[str]:
    """Extract common certification names from *text*."""
    cert_keywords = [
        "AWS Certified", "Azure Certified", "Google Professional", "GCP",
        "CPA", "PMP", "Certified", "CISSP", "CISA", "CEH", "CompTIA",
        "CKA", "CKAD", "Kubernetes", "Terraform Associate",
        "Scrum Master", "CSM", "ITIL", "Salesforce Certified",
        "TensorFlow Developer", "Professional Data Engineer",
    ]
    found = []
    for cert in cert_keywords:
        if re.search(r"\b" + re.escape(cert) + r"\b", text, re.IGNORECASE):
            found.append(cert)
    return found


def parse_resume(pdf_file, max_pages: int = 5) -> dict:
    """Parse a PDF resume and return a structured dictionary of extracted data."""
    text = extract_text(pdf_file, max_pages=max_pages)
    years_exp = extract_years_experience(text)
    return {
        "text": text,
        "email": extract_email(text),
        "phone": extract_phone(text),
        "years_experience": years_exp,
        "experience_level": detect_experience_level(text, years_exp),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "certifications": extract_certifications(text),
    }
