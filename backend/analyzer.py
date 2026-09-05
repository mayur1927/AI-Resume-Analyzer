"""NLP and heuristic evaluation engine for resume analysis and job compatibility.

This module uses rule-based NLP techniques (spaCy PhraseMatcher with canonical synonym
normalization, regex-based tokenization, structural heading detection, and weighted
ATS scoring heuristics). It does NOT require or depend on external LLM APIs, ensuring
deterministic, explainable, and viva-ready evaluation.
"""

import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Set, Tuple

import spacy
from spacy.matcher import PhraseMatcher

# Canonical skills and their common aliases / abbreviations
SKILL_TAXONOMY: Dict[str, List[str]] = {
    # Programming Languages
    "python": ["python", "python3", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java", "core java"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp", "c sharp"],
    "c": ["c language"],
    "go": ["go", "golang"],
    "rust": ["rust"],
    "ruby": ["ruby", "ruby on rails"],
    "php": ["php"],
    "sql": ["sql", "structured query language"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],

    # Web & Application Frameworks
    "react": ["react", "react.js", "reactjs"],
    "next.js": ["next.js", "nextjs", "next"],
    "angular": ["angular", "angular.js", "angularjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "node.js": ["node.js", "nodejs", "node"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "express": ["express", "express.js", "expressjs"],
    "spring boot": ["spring boot", "springboot", "spring framework"],
    "graphql": ["graphql"],
    "rest api": ["rest api", "rest apis", "restful api", "restful apis", "rest web services"],
    "microservices": ["microservices", "microservice architecture", "micro-services"],
    "tailwind css": ["tailwind css", "tailwind", "tailwindcss"],
    "bootstrap": ["bootstrap"],
    "streamlit": ["streamlit"],

    # Databases & Caching
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "sqlite": ["sqlite", "sqlite3"],
    "elasticsearch": ["elasticsearch", "elastic search"],
    "dynamodb": ["dynamodb"],
    "cassandra": ["cassandra"],

    # Cloud, DevOps & Infrastructure
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "google cloud": ["google cloud", "gcp", "google cloud platform"],
    "docker": ["docker", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git", "version control"],
    "github": ["github"],
    "gitlab": ["gitlab"],
    "ci/cd": ["ci/cd", "ci-cd", "cicd", "continuous integration", "continuous deployment"],
    "jenkins": ["jenkins"],
    "linux": ["linux", "unix", "ubuntu"],
    "terraform": ["terraform"],
    "nginx": ["nginx"],

    # Data Science, ML & Analytics
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "natural language processing": ["natural language processing", "nlp"],
    "spacy": ["spacy"],
    "data analysis": ["data analysis", "data analytics"],
    "data visualization": ["data visualization", "data viz"],
    "tableau": ["tableau"],
    "power bi": ["power bi", "powerbi"],
    "excel": ["excel", "microsoft excel", "ms excel"],
    "spark": ["spark", "apache spark", "pyspark"],
    "hadoop": ["hadoop", "apache hadoop"],
    "airflow": ["airflow", "apache airflow"],
    "kafka": ["kafka", "apache kafka"],
    "etl": ["etl", "data pipeline", "data pipelines", "etl pipelines"],
    "statistics": ["statistics", "statistical analysis", "statistical modeling"],

    # Testing & Engineering Practices
    "unit testing": ["unit testing", "unit tests", "automated testing", "test driven development", "tdd"],
    "pytest": ["pytest"],
    "agile": ["agile", "agile methodology"],
    "scrum": ["scrum"],
    "jira": ["jira"],
    "figma": ["figma"],
    "system design": ["system design", "software architecture"],
    "communication": ["communication", "verbal communication", "written communication"],
    "leadership": ["leadership", "team leadership", "mentorship"],
    "project management": ["project management"],
}

ALL_CANONICAL_SKILLS: List[str] = list(SKILL_TAXONOMY.keys())

# Comprehensive stop words and non-technical filler words for cleaner keyword comparison
STOP_WORDS: Set[str] = {
    # Common English stop words
    "and", "the", "with", "for", "that", "this", "from", "you", "your", "our", "are",
    "will", "have", "has", "using", "years", "year", "work", "team", "role", "job", "to",
    "of", "in", "a", "an", "on", "is", "be", "as", "or", "at", "by", "we", "it", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such", "than", "too",
    "very", "can", "did", "does", "doing", "down", "during", "few", "further", "had",
    "having", "her", "here", "hers", "herself", "him", "himself", "his", "how", "if",
    "into", "its", "itself", "just", "me", "might", "must", "my", "myself", "no", "nor",
    "not", "now", "off", "once", "only", "out", "over", "own", "same", "she", "should",
    "so", "some", "than", "then", "there", "these", "they", "this", "those", "through",
    "under", "until", "up", "was", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "would",
    # Resume / JD filler verbs and nouns
    "experience", "required", "requirements", "responsibilities", "qualification",
    "qualifications", "responsibilities", "candidate", "ability", "proficient",
    "seeking", "knowledge", "working", "understanding", "including", "across", "plus",
    "strong", "good", "great", "must", "needed", "opportunity", "environment", "position",
    "description", "details", "overview", "preferred", "duties", "task", "tasks",
}

# Initialize spaCy blank model and build PhraseMatcher with aliases
nlp = spacy.blank("en")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

for canonical, aliases in SKILL_TAXONOMY.items():
    patterns = [nlp.make_doc(alias) for alias in aliases]
    matcher.add(canonical, patterns)


@dataclass
class AnalysisResult:
    ats_score: int
    score_breakdown: Dict[str, int]
    resume_skills: List[str]
    job_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    suggestions: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


def extract_skills(text: str) -> List[str]:
    """Extract canonical skills from text using spaCy PhraseMatcher with alias normalization."""
    doc = nlp(text)
    matches = matcher(doc)
    
    found_canonicals: Set[str] = set()
    for match_id, _, _ in matches:
        canonical_name = nlp.vocab.strings[match_id]
        found_canonicals.add(canonical_name)
        
    # Return skills sorted in taxonomy order for deterministic output
    return [skill for skill in ALL_CANONICAL_SKILLS if skill in found_canonicals]


def important_keywords(text: str) -> Set[str]:
    """Extract significant keywords from text with noise filtering."""
    # Find words with 3+ alphanumeric/symbol characters
    raw_tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]{2,}\b", text.lower())
    
    # Strip trailing punctuation often left by sentence boundaries
    cleaned_tokens: Set[str] = set()
    for token in raw_tokens:
        clean = token.rstrip(".,;:!?'\"")
        if clean and clean not in STOP_WORDS and not clean.isnumeric():
            cleaned_tokens.add(clean)
            
    return cleaned_tokens


def section_score(resume_text: str) -> Tuple[int, List[str]]:
    """Evaluate presence of standard ATS resume sections."""
    text = resume_text.lower()
    
    section_patterns = {
        "experience": r"\b(experience|work history|employment|career history|professional background)\b",
        "education": r"\b(education|academic|qualifications|degree|university|college)\b",
        "skills": r"\b(skills|technical skills|technologies|core competencies|proficiencies|tech stack)\b",
        "projects": r"\b(project|projects|portfolio|key initiatives)\b",
        "summary": r"\b(summary|profile|about me|objective|professional summary|overview)\b",
    }
    
    detected: List[str] = [
        name for name, pattern in section_patterns.items() if re.search(pattern, text)
    ]
    
    pts = round((len(detected) / len(section_patterns)) * 10)
    return pts, detected


def formatting_score(resume_text: str) -> Tuple[int, bool, bool]:
    """Check basic contact and format constraints."""
    has_email = bool(re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", resume_text))
    length = len(resume_text)
    sensible_length = 250 <= length <= 12_000
    
    if has_email and sensible_length:
        score = 10
    elif has_email or sensible_length:
        score = 5
    else:
        score = 0
        
    return score, has_email, sensible_length


def build_suggestions(
    resume_text: str,
    missing_skills: List[str],
    matched_skills: List[str],
    detected_sections: List[str],
    has_email: bool,
    sensible_length: bool,
) -> List[str]:
    """Generate structured, actionable recommendations based on heuristic gaps."""
    suggestions: List[str] = []
    text = resume_text.lower()
    
    # 1. Skill Gap Recommendations
    if missing_skills:
        top_missing = missing_skills[:6]
        suggestions.append(
            f"Technical Skill Alignment: The job specification highlights skills not clearly demonstrated in your resume ({', '.join(top_missing)}). If you have experience with these tools, explicitly incorporate them into your Skills and Project descriptions."
        )
        
    # 2. Measurable Impact / Quantified Results
    has_metrics = bool(re.search(r"\b\d+(?:[,.]\d+)?\s*(%|x|users|projects|hours|days|months|ms|k|m|million|billion)\b", text))
    if not has_metrics:
        suggestions.append(
            "Quantify Accomplishments: Strengthen your bullet points with measurable engineering metrics (e.g., 'Reduced query latency by 35%', 'Supported 10k+ active users', or 'Automated 15+ weekly build tasks')."
        )
        
    # 3. Missing Structural Sections
    expected_sections = ["experience", "education", "skills", "projects", "summary"]
    missing_sections = [s.capitalize() for s in expected_sections if s not in detected_sections]
    if missing_sections:
        suggestions.append(
            f"Resume Structure: Consider adding dedicated sections for: {', '.join(missing_sections)} to ensure ATS parsers can categorize your qualifications easily."
        )
        
    # 4. Contact Information
    if not has_email:
        suggestions.append(
            "Contact Information: No valid email address was detected in the parsed text. Ensure your email is in a clear, text-readable header format rather than an embedded graphic."
        )
        
    # 5. Skill Density Check
    if len(matched_skills) < 3:
        suggestions.append(
            "Keyword Optimization: Resume has limited exact matches with the job requirements. Align technical terminology with the exact terms used in the target role specification."
        )
        
    if not suggestions:
        suggestions.append("Strong Alignment: Excellent overall match across technical competencies, section structure, and formatting. Tailor your executive summary to the specific role before applying.")
        
    return suggestions


def analyze_resume(resume_text: str, job_description: str) -> AnalysisResult:
    """Analyze resume against a job description and return explainable 0–100 match metrics.
    
    Scoring Weight Distribution:
    - Skill Vocabulary Match (60 pts max)
    - JD Keyword Alignment (20 pts max)
    - Document Structure & Sections (10 pts max)
    - Formatting & Contact Integrity (10 pts max)
    """
    # 1. Extract technical skills with canonical alias normalization
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)
    
    matched_skills = [skill for skill in job_skills if skill in resume_skills]
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]
    
    # 2. Compute Skill Match Score (Weighted 60%)
    if job_skills:
        skill_score = round((len(matched_skills) / len(job_skills)) * 60)
    else:
        # Fallback when JD has no specific technical vocabulary keywords
        skill_score = 30 if resume_skills else 15
        
    # 3. Compute Keyword Overlap Score (Weighted 20%)
    jd_keywords = important_keywords(job_description)
    resume_keywords = important_keywords(resume_text)
    
    if jd_keywords:
        keyword_overlap = len(jd_keywords & resume_keywords) / len(jd_keywords)
        keyword_score = round(keyword_overlap * 20)
    else:
        keyword_score = 10
        
    # 4. Structural Sections Check (Weighted 10%)
    sec_score, detected_sections = section_score(resume_text)
    
    # 5. Formatting & Contact Check (Weighted 10%)
    fmt_score, has_email, sensible_length = formatting_score(resume_text)
    
    # Total Composite ATS-style Score (0–100)
    total_score = min(100, skill_score + keyword_score + sec_score + fmt_score)
    
    # 6. Generate Rule-Based Recommendations
    suggestions = build_suggestions(
        resume_text=resume_text,
        missing_skills=missing_skills,
        matched_skills=matched_skills,
        detected_sections=detected_sections,
        has_email=has_email,
        sensible_length=sensible_length,
    )
    
    return AnalysisResult(
        ats_score=total_score,
        score_breakdown={
            "skill_match": skill_score,
            "keyword_match": keyword_score,
            "sections": sec_score,
            "formatting": fmt_score,
        },
        resume_skills=resume_skills,
        job_skills=job_skills,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        suggestions=suggestions,
    )
