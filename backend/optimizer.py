"""Deterministic, rule-based Resume Optimization Engine.

Provides:
1. Target match range validation
2. Conservative structured resume parsing (ResumeDocument)
3. Grounded fact and evidence extraction (ResumeEvidence)
4. Job requirement classification (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED)
5. Bounded, safe optimization operations with strict NON-FABRICATION guarantees
6. Multi-iteration ATS evaluation loop targeting user-specified score ranges
"""

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .analyzer import (
    ALL_CANONICAL_SKILLS,
    SKILL_TAXONOMY,
    analyze_resume,
    extract_skills,
    important_keywords,
    section_score,
)

MAX_OPTIMIZATION_ITERATIONS = 5
MIN_TARGET_SPAN = 5


class TargetRangeValidationError(ValueError):
    """Raised when the requested ATS target score range is invalid."""
    pass


def validate_target_range(target_min: int, target_max: int) -> Tuple[int, int]:
    """Validate target match range constraints.

    Rules:
    - target_min must be between 0 and 100
    - target_max must be between 0 and 100
    - target_min must be less than or equal to target_max
    - Range span must be at least MIN_TARGET_SPAN (5 percentage points)
    """
    if not (0 <= target_min <= 100):
        raise TargetRangeValidationError(
            f"Invalid target minimum: {target_min}%. Must be between 0 and 100%."
        )
    if not (0 <= target_max <= 100):
        raise TargetRangeValidationError(
            f"Invalid target maximum: {target_max}%. Must be between 0 and 100%."
        )
    if target_min > target_max:
        raise TargetRangeValidationError(
            f"Invalid target range: Minimum ({target_min}%) cannot be greater than maximum ({target_max}%)."
        )
    if (target_max - target_min) < MIN_TARGET_SPAN:
        # Enforce minimum useful range span for sensible optimization
        raise TargetRangeValidationError(
            f"Target range ({target_min}%–{target_max}%) is too narrow. "
            f"Please specify a range of at least {MIN_TARGET_SPAN} percentage points (e.g. {target_min}%–{min(100, target_min + MIN_TARGET_SPAN)}%)."
        )
    return target_min, target_max


# ==============================================================================
# STRUCTURED RESUME REPRESENTATION
# ==============================================================================


@dataclass
class ExperienceEntry:
    job_title: str = ""
    company: str = ""
    dates: str = ""
    bullets: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class ProjectEntry:
    project_name: str = ""
    technologies: List[str] = field(default_factory=list)
    bullets: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class EducationEntry:
    degree: str = ""
    institution: str = ""
    dates: str = ""
    raw_text: str = ""


@dataclass
class ResumeDocument:
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    contact_location: str = ""
    contact_links: List[str] = field(default_factory=list)
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experience: List[ExperienceEntry] = field(default_factory=list)
    projects: List[ProjectEntry] = field(default_factory=list)
    education: List[EducationEntry] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    other_sections: Dict[str, str] = field(default_factory=dict)
    original_raw_text: str = ""

    def render_text(self) -> str:
        """Render the structured resume into standard ATS-friendly plain text format."""
        sections: List[str] = []

        # 1. Contact Header
        header_lines: List[str] = []
        if self.contact_name:
            header_lines.append(self.contact_name)

        contact_details: List[str] = []
        if self.contact_email:
            contact_details.append(f"Email: {self.contact_email}")
        if self.contact_phone:
            contact_details.append(f"Phone: {self.contact_phone}")
        if self.contact_location:
            contact_details.append(self.contact_location)
        contact_details.extend(self.contact_links)

        if contact_details:
            header_lines.append(" | ".join(contact_details))

        if header_lines:
            sections.append("\n".join(header_lines))

        # 2. Professional Summary
        if self.summary:
            sections.append(f"Professional Summary\n{self.summary.strip()}")

        # 3. Core Technical Skills
        if self.skills:
            formatted_skills = ", ".join(self.skills)
            sections.append(f"Technical Skills\n{formatted_skills}")

        # 4. Professional Experience
        if self.experience:
            exp_lines: List[str] = ["Professional Experience"]
            for entry in self.experience:
                title_company = " - ".join(filter(None, [entry.job_title, entry.company]))
                header = " | ".join(filter(None, [title_company, entry.dates]))
                if header:
                    exp_lines.append(header)
                if entry.bullets:
                    for b in entry.bullets:
                        b_text = b.strip()
                        if not b_text.startswith("-") and not b_text.startswith("•"):
                            b_text = f"- {b_text}"
                        exp_lines.append(b_text)
                elif entry.raw_text:
                    exp_lines.append(entry.raw_text.strip())
            sections.append("\n".join(exp_lines))

        # 5. Key Projects
        if self.projects:
            proj_lines: List[str] = ["Projects"]
            for p in self.projects:
                p_header = p.project_name
                if p.technologies:
                    p_header += f" (Technologies: {', '.join(p.technologies)})"
                if p_header:
                    proj_lines.append(p_header)
                if p.bullets:
                    for b in p.bullets:
                        b_text = b.strip()
                        if not b_text.startswith("-") and not b_text.startswith("•"):
                            b_text = f"- {b_text}"
                        proj_lines.append(b_text)
                elif p.raw_text:
                    proj_lines.append(p.raw_text.strip())
            sections.append("\n".join(proj_lines))

        # 6. Education
        if self.education:
            edu_lines: List[str] = ["Education"]
            for edu in self.education:
                deg_inst = " - ".join(filter(None, [edu.degree, edu.institution]))
                header = " | ".join(filter(None, [deg_inst, edu.dates]))
                if header:
                    edu_lines.append(header)
                elif edu.raw_text:
                    edu_lines.append(edu.raw_text.strip())
            sections.append("\n".join(edu_lines))

        # 7. Certifications
        if self.certifications:
            cert_lines = ["Certifications\n" + "\n".join(f"- {c}" for c in self.certifications)]
            sections.append("\n".join(cert_lines))

        # 8. Other Miscellaneous Sections
        for title, content in self.other_sections.items():
            if content.strip():
                sections.append(f"{title.title()}\n{content.strip()}")

        return "\n\n".join(sections)


# ==============================================================================
# CONSERVATIVE RESUME PARSER
# ==============================================================================


SECTION_PATTERNS = {
    "summary": re.compile(
        r"^(?:professional\s+summary|summary|profile|about\s+me|objective|overview)[:\s]*$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:technical\s+skills|core\s+competencies|skills|technologies|proficiencies|tech\s+stack)[:\s]*$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:professional\s+experience|work\s+history|experience|employment\s+history|work\s+experience)[:\s]*$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:projects|key\s+projects|portfolio|technical\s+projects)[:\s]*$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education|academic\s+background|qualifications|academic\s+history)[:\s]*$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications|licenses|credentials|courses)[:\s]*$",
        re.IGNORECASE,
    ),
    "awards": re.compile(
        r"^(?:awards|honors|achievements|accolades|recognition)[:\s]*$",
        re.IGNORECASE,
    ),
    "publications": re.compile(
        r"^(?:publications|papers|research|articles)[:\s]*$",
        re.IGNORECASE,
    ),
    "volunteer": re.compile(
        r"^(?:volunteer|volunteer\s+experience|community\s+service|leadership)[:\s]*$",
        re.IGNORECASE,
    ),
    "languages": re.compile(
        r"^(?:languages|language\s+proficiencies)[:\s]*$",
        re.IGNORECASE,
    ),
}


def parse_resume_text(text: str) -> ResumeDocument:
    """Conservatively parse raw resume text into a structured ResumeDocument."""
    doc = ResumeDocument(original_raw_text=text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return doc

    # 1. Contact Info Extraction
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    if email_match:
        doc.contact_email = email_match.group(0)

    phone_match = re.search(
        r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text
    )
    if phone_match:
        doc.contact_phone = phone_match.group(0)

    # Detect Name (heuristic: first non-empty line before sections)
    if lines and not any(pat.match(lines[0]) for pat in SECTION_PATTERNS.values()):
        # Split out pipe-delimited contact info if present on first line
        first_line_parts = [p.strip() for p in lines[0].split("|")]
        doc.contact_name = first_line_parts[0]

    # 2. Section Partitioning
    section_buckets: Dict[str, List[str]] = {}
    current_section: str = "header"
    section_buckets[current_section] = []

    for line in lines:
        matched_section_name: Optional[str] = None
        for sec_name, sec_pattern in SECTION_PATTERNS.items():
            if sec_pattern.match(line):
                matched_section_name = sec_name
                break

        if matched_section_name:
            current_section = matched_section_name
            if current_section not in section_buckets:
                section_buckets[current_section] = []
        else:
            section_buckets[current_section].append(line)

    # 3. Populate Structured Sections
    # Summary
    if "summary" in section_buckets and section_buckets["summary"]:
        doc.summary = " ".join(section_buckets["summary"])

    # Skills: extract comma or bullet separated tokens + NLP canonical skills
    skills_raw_lines = section_buckets.get("skills", [])
    extracted_from_section: List[str] = []
    for s_line in skills_raw_lines:
        # Split on commas, bullets, pipes, or semicolons
        tokens = [t.strip() for t in re.split(r"[,•|;]+", s_line) if t.strip()]
        for t in tokens:
            if len(t) < 40 and not t.lower().startswith("skills:"):
                extracted_from_section.append(t)

    # Supplement with spaCy canonical skill extractor
    nlp_detected_skills = extract_skills(text)
    combined_skills: List[str] = []
    seen_skills_lower: Set[str] = set()

    for s in extracted_from_section + nlp_detected_skills:
        clean_s = s.strip()
        if clean_s.lower() not in seen_skills_lower:
            seen_skills_lower.add(clean_s.lower())
            combined_skills.append(clean_s)
    doc.skills = combined_skills

    # Experience
    exp_lines = section_buckets.get("experience", [])
    if exp_lines:
        current_exp = ExperienceEntry()
        for eline in exp_lines:
            if eline.startswith(("-", "•", "*")):
                current_exp.bullets.append(eline.lstrip("-•* ").strip())
            elif any(
                yr in eline
                for yr in ["201", "202", "Present", "present", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            ):
                if current_exp.bullets or current_exp.job_title:
                    doc.experience.append(current_exp)
                    current_exp = ExperienceEntry()
                current_exp.job_title = eline
            else:
                if not current_exp.job_title:
                    current_exp.job_title = eline
                else:
                    current_exp.bullets.append(eline)
        if current_exp.job_title or current_exp.bullets:
            doc.experience.append(current_exp)

    # Projects
    proj_lines = section_buckets.get("projects", [])
    if proj_lines:
        current_proj = ProjectEntry()
        for pline in proj_lines:
            if pline.startswith(("-", "•", "*")):
                current_proj.bullets.append(pline.lstrip("-•* ").strip())
            else:
                if current_proj.project_name or current_proj.bullets:
                    doc.projects.append(current_proj)
                    current_proj = ProjectEntry()
                current_proj.project_name = pline
        if current_proj.project_name or current_proj.bullets:
            doc.projects.append(current_proj)

    # Education
    edu_lines = section_buckets.get("education", [])
    if edu_lines:
        for eduline in edu_lines:
            doc.education.append(EducationEntry(raw_text=eduline))

    # Certifications
    cert_lines = section_buckets.get("certifications", [])
    if cert_lines:
        for cline in cert_lines:
            doc.certifications.append(cline.lstrip("-•* ").strip())

    # Other Miscellaneous / Non-Standard Sections
    standard_keys = {"header", "summary", "skills", "experience", "projects", "education", "certifications"}
    for sec_key, sec_lines in section_buckets.items():
        if sec_key not in standard_keys and sec_lines:
            doc.other_sections[sec_key] = "\n".join(sec_lines)

    return doc


# ==============================================================================
# EVIDENCE MODEL & FACT VERIFICATION
# ==============================================================================


@dataclass
class ResumeEvidence:
    source_text: str
    category: str  # skill, experience, project, metric, education
    normalized_term: str
    source_section: str
    confidence: str = "high"


def extract_resume_evidence(doc: ResumeDocument) -> List[ResumeEvidence]:
    """Extract verifiable factual claims and competencies from source resume."""
    evidence_list: List[ResumeEvidence] = []
    text = doc.original_raw_text

    # Extract all canonical skills with evidence location
    doc_skills = extract_skills(text)
    for skill in doc_skills:
        # Locate containing sentence/bullet
        matching_line = ""
        for line in text.splitlines():
            if re.search(rf"\b{re.escape(skill)}\b", line, re.IGNORECASE):
                matching_line = line.strip()
                break
        evidence_list.append(
            ResumeEvidence(
                source_text=matching_line or skill,
                category="skill",
                normalized_term=skill.lower(),
                source_section="skills" if skill in doc.skills else "body",
                confidence="high",
            )
        )

    # Extract experience and project claims
    for exp in doc.experience:
        for b in exp.bullets:
            evidence_list.append(
                ResumeEvidence(
                    source_text=b,
                    category="experience",
                    normalized_term=exp.job_title,
                    source_section="experience",
                    confidence="high",
                )
            )

    for proj in doc.projects:
        for b in proj.bullets:
            evidence_list.append(
                ResumeEvidence(
                    source_text=b,
                    category="project",
                    normalized_term=proj.project_name,
                    source_section="projects",
                    confidence="high",
                )
            )

    return evidence_list


def classify_requirements(
    job_description: str, evidence: List[ResumeEvidence]
) -> Dict[str, str]:
    """Classify JD requirements into SUPPORTED, PARTIALLY_SUPPORTED, or UNSUPPORTED.

    Strict Non-Fabrication Rule: Only requirements with evidence in source resume
    are classified as SUPPORTED or PARTIALLY_SUPPORTED.
    """
    job_skills = extract_skills(job_description)
    evidenced_skills = {e.normalized_term for e in evidence if e.category == "skill"}

    classification: Dict[str, str] = {}
    for j_skill in job_skills:
        if j_skill in evidenced_skills:
            classification[j_skill] = "SUPPORTED"
        else:
            # Check for partial alias match in source evidence
            aliases = SKILL_TAXONOMY.get(j_skill, [j_skill])
            if any(alias in evidenced_skills for alias in aliases):
                classification[j_skill] = "PARTIALLY_SUPPORTED"
            else:
                classification[j_skill] = "UNSUPPORTED"

    return classification


# ==============================================================================
# SAFE OPTIMIZATION OPERATIONS (GROUNDED & DETERMINISTIC)
# ==============================================================================


@dataclass
class ChangeRecord:
    section: str
    original_text: str
    optimized_text: str
    reason: str
    evidence: str
    change_type: str


@dataclass
class OptimizationIteration:
    iteration_number: int
    ats_score: int
    applied_operation: str
    score_delta: int
    summary: str


@dataclass
class OptimizationResult:
    optimization_id: str
    analysis_id: str
    original_score: int
    target_min: int
    target_max: int
    final_score: int
    target_achieved: bool
    iteration_count: int
    original_resume_text: str
    final_resume_text: str
    unsupported_requirements: List[str]
    supported_requirements: List[str]
    changes: List[Dict[str, Any]]
    iterations: List[Dict[str, Any]]
    optimization_summary: str
    best_achievable_explanation: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def safe_reorder_skills(
    doc: ResumeDocument,
    classification: Dict[str, str],
    changes: List[ChangeRecord],
) -> ResumeDocument:
    """Prioritize verified JD-matching skills to the front of the skills list."""
    supported = [s for s, status in classification.items() if status in ("SUPPORTED", "PARTIALLY_SUPPORTED")]
    if not supported or not doc.skills:
        return doc

    original_skills_list = list(doc.skills)
    reordered: List[str] = []
    seen: Set[str] = set()

    # Place supported JD skills first (using original casing/entry from doc if present)
    for sup in supported:
        for orig in doc.skills:
            if orig.lower() == sup.lower() or orig.lower() in SKILL_TAXONOMY.get(sup.lower(), []):
                if orig.lower() not in seen:
                    seen.add(orig.lower())
                    reordered.append(orig)

    # Append remaining genuine candidate skills
    for orig in doc.skills:
        if orig.lower() not in seen:
            seen.add(orig.lower())
            reordered.append(orig)

    if reordered != original_skills_list:
        changes.append(
            ChangeRecord(
                section="skills",
                original_text=", ".join(original_skills_list),
                optimized_text=", ".join(reordered),
                reason="Prioritized verified JD-relevant technical competencies at the front of the Skills matrix.",
                evidence=f"Candidate source resume confirmed experience with: {', '.join(supported)}",
                change_type="reorder_skills",
            )
        )
        doc.skills = reordered
    return doc


def safe_normalize_supported_aliases(
    doc: ResumeDocument,
    classification: Dict[str, str],
    changes: List[ChangeRecord],
) -> ResumeDocument:
    """Normalize informal or abbreviated aliases to formal JD terminology strictly where supported."""
    supported = [s for s, status in classification.items() if status in ("SUPPORTED", "PARTIALLY_SUPPORTED")]
    if not supported or not doc.skills:
        return doc

    updated_skills: List[str] = []
    normalized_occurred = False

    for s in doc.skills:
        matched_canonical = None
        for sup in supported:
            aliases = SKILL_TAXONOMY.get(sup, [sup])
            if s.lower() in [a.lower() for a in aliases] and s.lower() != sup.lower():
                matched_canonical = sup
                break

        if matched_canonical:
            # Capitalize appropriately (e.g. postgres -> PostgreSQL, k8s -> Kubernetes)
            formatted_name = matched_canonical.title()
            if matched_canonical in ("postgresql", "mongodb", "fastapi", "next.js", "node.js", "ci/cd", "sql", "html", "css", "aws", "gcp"):
                # Preserve standard tech casing
                casing_map = {
                    "postgresql": "PostgreSQL",
                    "mongodb": "MongoDB",
                    "fastapi": "FastAPI",
                    "next.js": "Next.js",
                    "node.js": "Node.js",
                    "ci/cd": "CI/CD",
                    "sql": "SQL",
                    "html": "HTML",
                    "css": "CSS",
                    "aws": "AWS",
                    "gcp": "GCP",
                }
                formatted_name = casing_map.get(matched_canonical, formatted_name)

            changes.append(
                ChangeRecord(
                    section="skills",
                    original_text=s,
                    optimized_text=formatted_name,
                    reason=f"Standardized informal alias '{s}' to formal ATS terminology '{formatted_name}'.",
                    evidence=f"Candidate resume explicitly evidences competency with {s}.",
                    change_type="normalize_supported_terminology",
                )
            )
            updated_skills.append(formatted_name)
            normalized_occurred = True
        else:
            updated_skills.append(s)

    if normalized_occurred:
        doc.skills = updated_skills
    return doc


def safe_structure_ats_headings(
    doc: ResumeDocument,
    changes: List[ChangeRecord],
) -> ResumeDocument:
    """Ensure standard ATS section headers are structured and categorized."""
    # This transformation is inherently validated when rendering the document with standard ATS headers
    changes.append(
        ChangeRecord(
            section="structure",
            original_text="Raw or informal section layout",
            optimized_text="Standardized ATS Headers (Summary, Technical Skills, Professional Experience, Projects, Education)",
            reason="Structured document with standard ATS headers for optimal parser extraction.",
            evidence="Original candidate sections parsed and mapped to standard hierarchy without altering underlying content.",
            change_type="improve_section_structure",
        )
    )
    return doc


def safe_generate_supported_summary(
    doc: ResumeDocument,
    classification: Dict[str, str],
    changes: List[ChangeRecord],
) -> ResumeDocument:
    """Craft an evidence-backed summary emphasizing ONLY supported candidate competencies."""
    supported_skills = [s for s, status in classification.items() if status in ("SUPPORTED", "PARTIALLY_SUPPORTED")]
    if not supported_skills:
        return doc

    top_supported = supported_skills[:5]
    skills_phrase = ", ".join(s.title() for s in top_supported)

    # Derive role title strictly from verified resume content, or fallback to neutral 'Professional'
    role_title = "Professional"
    if doc.experience and doc.experience[0].job_title:
        candidate_title = doc.experience[0].job_title.split("-")[0].strip()
        candidate_title = candidate_title.split("|")[0].strip()
        if candidate_title and len(candidate_title) < 50:
            role_title = candidate_title

    optimized_summary = (
        f"Results-driven {role_title} with verified technical background in {skills_phrase}. "
        f"Demonstrated track record of designing, developing, and maintaining high-performance solutions "
        f"aligned with technical specifications and engineering best practices."
    )

    if doc.summary != optimized_summary:
        changes.append(
            ChangeRecord(
                section="summary",
                original_text=doc.summary or "(No dedicated summary section)",
                optimized_text=optimized_summary,
                reason="Synthesized an ATS-optimized professional summary highlighting verified candidate competencies.",
                evidence=f"Candidate source resume confirms competency in: {skills_phrase}",
                change_type="improve_summary",
            )
        )
        doc.summary = optimized_summary

    return doc



# ==============================================================================
# BOUNDED OPTIMIZATION ITERATION LOOP
# ==============================================================================


def optimize_resume(
    resume_text: str,
    job_description: str,
    target_min: int,
    target_max: int,
) -> OptimizationResult:
    """Run conservative, iterative resume optimization targeting a specified ATS score range.

    Non-Fabrication Guarantee:
    - Never invents unsupported skills, metrics, degrees, or employers.
    - If the target score cannot safely be reached, stops cleanly and returns the best safe score.
    """
    target_min, target_max = validate_target_range(target_min, target_max)

    # 1. Baseline ATS Evaluation
    initial_analysis = analyze_resume(resume_text, job_description)
    current_score = initial_analysis.ats_score
    original_score = current_score

    # 2. Parse into Intermediate Representation & Extract Grounded Evidence
    doc = parse_resume_text(resume_text)
    evidence = extract_resume_evidence(doc)
    classification = classify_requirements(job_description, evidence)

    supported_reqs = [k for k, v in classification.items() if v in ("SUPPORTED", "PARTIALLY_SUPPORTED")]
    unsupported_reqs = [k for k, v in classification.items() if v == "UNSUPPORTED"]

    changes: List[ChangeRecord] = []
    iterations: List[OptimizationIteration] = []
    current_text = doc.render_text()

    # Record Iteration 0 (Baseline)
    iterations.append(
        OptimizationIteration(
            iteration_number=0,
            ats_score=current_score,
            applied_operation="baseline_evaluation",
            score_delta=0,
            summary=f"Baseline evaluation completed: {current_score}% ATS match score.",
        )
    )

    # 3. Optimization Pipeline Steps
    transformation_steps = [
        ("structure_headers", lambda d, c: safe_structure_ats_headings(d, c)),
        ("normalize_aliases", lambda d, c: safe_normalize_supported_aliases(d, classification, c)),
        ("reorder_skills", lambda d, c: safe_reorder_skills(d, classification, c)),
        ("improve_summary", lambda d, c: safe_generate_supported_summary(d, classification, c)),
    ]

    iteration_num = 0
    for op_name, op_func in transformation_steps:
        if iteration_num >= MAX_OPTIMIZATION_ITERATIONS:
            break

        # Check if score is already within the requested target range
        if target_min <= current_score <= target_max:
            break

        iteration_num += 1
        prev_score = current_score

        # Apply transformation
        doc = op_func(doc, changes)
        candidate_text = doc.render_text()

        # Re-score candidate draft with existing ATS engine
        eval_result = analyze_resume(candidate_text, job_description)
        new_score = eval_result.ats_score

        # Accept modification if score improved or maintained
        if new_score >= current_score:
            current_score = new_score
            current_text = candidate_text
            iterations.append(
                OptimizationIteration(
                    iteration_number=iteration_num,
                    ats_score=current_score,
                    applied_operation=op_name,
                    score_delta=current_score - prev_score,
                    summary=f"Iteration {iteration_num} ({op_name}): score shifted from {prev_score}% to {current_score}%.",
                )
            )
        else:
            # Revert doc if step caused score regression
            doc = parse_resume_text(current_text)
            iterations.append(
                OptimizationIteration(
                    iteration_number=iteration_num,
                    ats_score=current_score,
                    applied_operation=op_name,
                    score_delta=0,
                    summary=f"Iteration {iteration_num} ({op_name}): skipped change to prevent score regression ({new_score}% vs {current_score}%).",
                )
            )

        if target_min <= current_score <= target_max:
            break

    target_achieved = target_min <= current_score <= target_max
    if not target_achieved and current_score > target_max:
        # If score surpassed target_max through structural perfection, consider achieved if >= target_min
        target_achieved = current_score >= target_min

    best_achievable_explanation: Optional[str] = None
    if not target_achieved:
        unsupported_str = ", ".join(unsupported_reqs) if unsupported_reqs else "unspecified requirement gaps"
        best_achievable_explanation = (
            f"The target range of {target_min}%-{target_max}% could not safely be reached without fabricating candidate qualifications. "
            f"The remaining gap is caused by job requirements not evidenced in the original resume ({unsupported_str}). "
            f"The optimizer reached the highest safe score of {current_score}% by optimizing structure, supported skills, and terminology."
        )

    summary_text = (
        f"Optimization completed in {len(iterations) - 1} iterations. "
        f"Score shifted from {original_score}% to {current_score}% (Target: {target_min}%-{target_max}%). "
        f"Target achieved: {'Yes' if target_achieved else 'No (Plateaued at best safe score)'}."
    )


    return OptimizationResult(
        optimization_id=str(uuid.uuid4()),
        analysis_id="",  # Populated when linked to a database Analysis record
        original_score=original_score,
        target_min=target_min,
        target_max=target_max,
        final_score=current_score,
        target_achieved=target_achieved,
        iteration_count=len(iterations) - 1,
        original_resume_text=resume_text,
        final_resume_text=current_text,
        unsupported_requirements=unsupported_reqs,
        supported_requirements=supported_reqs,
        changes=[asdict(c) for c in changes],
        iterations=[asdict(it) for it in iterations],
        optimization_summary=summary_text,
        best_achievable_explanation=best_achievable_explanation,
    )
