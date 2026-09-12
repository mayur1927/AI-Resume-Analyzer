"""Comprehensive automated test suite for Phase 2: AI Resume Optimizer.

Verifies:
1. Target match range validation (constraints, bounds, minimum span).
2. Intermediate representation parsing and fact extraction.
3. Strict non-fabrication guarantee (unsupported requirements are excluded).
4. Role fallback neutrality (no assumed "Software Engineer" title).
5. Deterministic optimization loop and plateau explanation.
6. FastAPI endpoints (/api/optimize, /api/optimizations, /api/optimizations/{id}).
7. Analysis-ID optimization workflow & cross-session security isolation.
"""

import io
import os
import sys
import uuid
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.main import app
from backend.optimizer import (
    MIN_TARGET_SPAN,
    ResumeDocument,
    TargetRangeValidationError,
    classify_requirements,
    extract_resume_evidence,
    optimize_resume,
    parse_resume_text,
    validate_target_range,
)


def create_test_pdf(text: str) -> bytes:
    """Generate a valid, in-memory PDF with readable text."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in text.split("\n"):
        if line.strip():
            pdf.drawString(50, y, line.strip())
            y -= 15
            if y < 50:
                pdf.showPage()
                y = 750
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


SAMPLE_RESUME_TEXT = """
Alex Morgan
Email: alex.morgan@example.com | Phone: (555) 234-5678 | San Francisco, CA

Professional Summary
Experienced Software Engineer with 4 years building scalable web services and backend APIs.

Technical Skills
Python, FastAPI, PostgreSQL, Docker, Git, REST APIs, Redis, SQL, PyTorch

Professional Experience
Software Engineer - Tech Innovations Inc. | 2021 - Present
- Designed and maintained RESTful microservices in Python and FastAPI handling 1M daily requests.
- Optimized PostgreSQL database queries, reducing latency by 35%.
- Implemented Docker containerization and CI/CD pipelines.

Education
B.S. in Computer Science - University of California, Berkeley | 2020
"""

UNOPTIMIZED_RESUME_TEXT = """
Alex Morgan
alex.morgan@example.com | 555-234-5678

About Me
Working on software applications.

Things I know:
python, postgres, docker, fastapi, git

Work History:
Developer at Tech Corp (2022-Present)
- Built web services in python.
"""

SAMPLE_JD_MATCHING = """
We are seeking a Backend Software Engineer with strong experience in Python, FastAPI, PostgreSQL, Docker, and REST APIs.
The candidate will design scalable backend systems, optimize SQL database queries, and deploy containerized services.
"""

SAMPLE_JD_UNSUPPORTED = """
We are looking for a Senior Blockchain & Distributed Systems Architect.
Required Skills: Rust, Solidity, WebAssembly, Kubernetes, GraphQL, Golang, Elixir, Haskell.
The role requires developing smart contracts and building consensus protocols.
"""


def test_target_range_validation():
    print("\n--- Test 1: Target Match Range Validation ---")
    # Valid ranges
    assert validate_target_range(80, 85) == (80, 85)
    assert validate_target_range(70, 90) == (70, 90)
    assert validate_target_range(0, 100) == (0, 100)

    # Invalid: min > max
    try:
        validate_target_range(85, 80)
        assert False, "Should have raised TargetRangeValidationError for min > max"
    except TargetRangeValidationError:
        pass

    # Invalid: span < MIN_TARGET_SPAN
    try:
        validate_target_range(80, 82)
        assert False, f"Should have raised TargetRangeValidationError for span < {MIN_TARGET_SPAN}"
    except TargetRangeValidationError:
        pass

    # Invalid: out of bounds
    try:
        validate_target_range(-5, 80)
        assert False, "Should have raised for negative min"
    except TargetRangeValidationError:
        pass

    try:
        validate_target_range(80, 105)
        assert False, "Should have raised for max > 100"
    except TargetRangeValidationError:
        pass

    print("[PASS] Target match range validation enforced all constraints correctly.")


def test_intermediate_representation_and_non_fabrication():
    print("\n--- Test 2: Structured IR & Non-Fabrication Fact Model ---")
    doc = parse_resume_text(SAMPLE_RESUME_TEXT)
    assert doc.contact_email == "alex.morgan@example.com"
    assert "Python" in doc.skills or "python" in [s.lower() for s in doc.skills]
    assert len(doc.experience) >= 1

    evidence = extract_resume_evidence(doc)
    evidenced_skills = {e.normalized_term for e in evidence if e.category == "skill"}
    assert "python" in evidenced_skills
    assert "fastapi" in evidenced_skills
    assert "docker" in evidenced_skills

    # Classify against matching JD
    classif_matching = classify_requirements(SAMPLE_JD_MATCHING, evidence)
    assert classif_matching.get("python") == "SUPPORTED"
    assert classif_matching.get("fastapi") == "SUPPORTED"

    # Classify against unsupported JD
    classif_unsupported = classify_requirements(SAMPLE_JD_UNSUPPORTED, evidence)
    assert classif_unsupported.get("rust") == "UNSUPPORTED"
    assert classif_unsupported.get("kubernetes") == "UNSUPPORTED"
    assert classif_unsupported.get("graphql") == "UNSUPPORTED"

    # Run optimizer against unsupported JD
    result = optimize_resume(SAMPLE_RESUME_TEXT, SAMPLE_JD_UNSUPPORTED, target_min=80, target_max=85)

    # CRITICAL NON-FABRICATION ASSERTION:
    # Final optimized resume must NOT contain unsupported skills that were not in original
    for unsupp in ["rust", "solidity", "webassembly", "kubernetes", "graphql", "golang", "elixir", "haskell"]:
        assert unsupp not in result.final_resume_text.lower(), f"Fabrication violation: {unsupp} found in optimized resume!"

    assert not result.target_achieved, "Should not achieve 80-85% match when all requirements are unsupported"
    assert result.best_achievable_explanation is not None
    assert "unsupported" in result.best_achievable_explanation.lower() or "fabricating" in result.best_achievable_explanation.lower()

    # Recheck with pure "Python developer" vs "FastAPI, AWS, Kubernetes"
    py_only_resume = "Taylor Smith\ntaylor@example.com\n\nTechnical Skills\nPython\n\nExperience\nPython Developer (2022-Present)\n- Built python scripts."
    py_jd = "Senior Architect with FastAPI, AWS, and Kubernetes experience."
    res_py = optimize_resume(py_only_resume, py_jd, target_min=75, target_max=90)
    for forbidden in ["fastapi", "aws", "kubernetes"]:
        assert forbidden not in res_py.final_resume_text.lower(), f"Fabrication violation: {forbidden} injected into python-only resume!"
    assert not res_py.target_achieved

    print("[PASS] Non-fabrication guarantee verified: Zero unsupported skills fabricated across all test scenarios.")


def test_role_fallback_neutrality():
    print("\n--- Test 3: Role Fallback Neutrality (No assumed 'Software Engineer') ---")

    # Case A: Resume with Python & SQL, no title, no summary
    data_analyst_resume = """
Jordan Lee
jordan.lee@example.com | 555-123-4567

Technical Skills
Python, SQL, Tableau, Excel

Education
B.S. in Statistics - University of Michigan | 2021
"""
    data_analyst_jd = """
We are seeking a Data Analyst skilled in Python, SQL, Tableau, and data modeling to deliver business insights.
"""
    # Use target_min=80 to trigger summary generation
    res_da = optimize_resume(data_analyst_resume, data_analyst_jd, target_min=80, target_max=95)

    # Assert generated summary does NOT assume "Software Engineer"
    assert "Software Engineer" not in res_da.final_resume_text, "Assumption violation: Inferred 'Software Engineer' for unclassified resume!"
    assert "Professional" in res_da.final_resume_text, "Expected neutral 'Professional' role title fallback"

    # Case B: Resume with explicit job title "Data Analyst"
    titled_resume = """
Sam Taylor
sam@example.com | 555-987-6543

Experience
Data Analyst - Analytics Corp | 2021 - Present
- Analyzed dataset trends in Python and SQL.

Technical Skills
Python, SQL, Pandas
"""
    res_titled = optimize_resume(titled_resume, data_analyst_jd, target_min=80, target_max=95)
    assert "Data Analyst" in res_titled.final_resume_text, "Expected explicit title 'Data Analyst' to be preserved"
    assert "Software Engineer" not in res_titled.final_resume_text
    print("[PASS] Role fallback neutrality verified: 'Software Engineer' is never invented for non-engineering or untitled resumes.")


def test_target_achievement_with_supported_evidence():
    print("\n--- Test 4: Optimization with Supported Evidence ---")
    # Subtest 4A: Target reachable with safe optimization
    result_achieved = optimize_resume(UNOPTIMIZED_RESUME_TEXT, SAMPLE_JD_MATCHING, target_min=60, target_max=75)
    assert result_achieved.final_score >= result_achieved.original_score
    assert len(result_achieved.changes) >= 1
    assert result_achieved.target_achieved
    print(f"[PASS 4A] Reachable Target: {result_achieved.original_score}% -> {result_achieved.final_score}% (Target Achieved: {result_achieved.target_achieved})")

    # Subtest 4B: Target safely unreachable without fabrication -> Plateau handled gracefully
    result_plateau = optimize_resume(UNOPTIMIZED_RESUME_TEXT, SAMPLE_JD_MATCHING, target_min=85, target_max=95)
    assert not result_plateau.target_achieved
    assert result_plateau.best_achievable_explanation is not None
    assert len(result_plateau.unsupported_requirements) >= 1
    print(f"[PASS 4B] Plateau Target: Reached best safe score {result_plateau.final_score}% without fabricating {result_plateau.unsupported_requirements}")


def test_fastapi_endpoints_and_session_isolation():
    print("\n--- Test 5: FastAPI Endpoints & Session Isolation ---")
    client_a = TestClient(app)
    client_b = TestClient(app)

    # 1. User A runs optimization via PDF upload
    pdf_bytes = create_test_pdf(UNOPTIMIZED_RESUME_TEXT)
    response_a = client_a.post(
        "/api/optimize",
        files={"resume": ("alex_resume.pdf", pdf_bytes, "application/pdf")},
        data={
            "job_description": SAMPLE_JD_MATCHING,
            "target_min": 60,
            "target_max": 75,
        },
    )
    assert response_a.status_code == 200, f"Optimize failed: {response_a.text}"
    data_a = response_a.json()
    opt_id_a = data_a["optimization_id"]
    assert opt_id_a
    assert data_a["target_min"] == 60
    assert data_a["target_max"] == 75

    # 2. User A fetches single optimization
    get_res_a = client_a.get(f"/api/optimizations/{opt_id_a}")
    assert get_res_a.status_code == 200
    assert get_res_a.json()["optimization_id"] == opt_id_a

    # 3. User A lists optimizations
    list_res_a = client_a.get("/api/optimizations")
    assert list_res_a.status_code == 200
    opt_ids_a = [item["optimization_id"] for item in list_res_a.json()]
    assert opt_id_a in opt_ids_a

    # 4. User B (different session) CANNOT access User A's optimization
    get_res_b = client_b.get(f"/api/optimizations/{opt_id_a}")
    assert get_res_b.status_code == 404, f"Privacy violation: User B accessed User A's optimization! Status: {get_res_b.status_code}"

    # 5. User B list MUST NOT contain User A's optimization
    list_res_b = client_b.get("/api/optimizations")
    assert list_res_b.status_code == 200
    opt_ids_b = [item["optimization_id"] for item in list_res_b.json()]
    assert opt_id_a not in opt_ids_b

    # 6. Test invalid target range rejection via API
    invalid_res = client_a.post(
        "/api/optimize",
        files={"resume": ("alex_resume.pdf", pdf_bytes, "application/pdf")},
        data={
            "job_description": SAMPLE_JD_MATCHING,
            "target_min": 90,
            "target_max": 80,  # min > max
        },
    )
    assert invalid_res.status_code == 422, f"Expected 422 for invalid range, got {invalid_res.status_code}"

    print("[PASS] API optimization endpoints and multi-user session isolation verified successfully.")


def test_optimization_via_analysis_id_and_cross_session_security():
    print("\n--- Test 6: Optimization via analysis_id & Cross-Session Security ---")
    client_a = TestClient(app)
    client_b = TestClient(app)

    # 1. Session A performs initial analysis
    pdf_bytes = create_test_pdf(SAMPLE_RESUME_TEXT)
    analyze_res = client_a.post(
        "/api/analyze",
        files={"resume": ("alex_sample.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": SAMPLE_JD_MATCHING},
    )
    assert analyze_res.status_code == 200, f"Analysis failed: {analyze_res.text}"
    analyze_data = analyze_res.json()
    analysis_id = analyze_data["analysis_id"]
    initial_score = analyze_data["ats_score"]
    assert analysis_id

    # 2. Session A requests optimization referencing analysis_id (no file upload)
    opt_res = client_a.post(
        "/api/optimize",
        data={
            "analysis_id": analysis_id,
            "job_description": SAMPLE_JD_MATCHING,
            "target_min": 85,
            "target_max": 95,
        },
    )
    assert opt_res.status_code == 200, f"Optimization via analysis_id failed: {opt_res.text}"
    opt_data = opt_res.json()
    assert opt_data["analysis_id"] == analysis_id, "Optimization must reference parent analysis_id"
    assert opt_data["original_score"] == initial_score, "Original score must match initial analysis score"
    assert "final_score" in opt_data
    assert "changes" in opt_data
    opt_id = opt_data["optimization_id"]

    # 3. Session A verifies optimization is in history
    get_opt_a = client_a.get(f"/api/optimizations/{opt_id}")
    assert get_opt_a.status_code == 200
    assert get_opt_a.json()["analysis_id"] == analysis_id

    # 4. Cross-session security check: Session B attempts to optimize Session A's analysis_id
    cross_opt_res = client_b.post(
        "/api/optimize",
        data={
            "analysis_id": analysis_id,
            "job_description": SAMPLE_JD_MATCHING,
            "target_min": 85,
            "target_max": 95,
        },
    )
    assert cross_opt_res.status_code == 404, f"Security vulnerability: Session B optimized Session A's analysis! Status: {cross_opt_res.status_code}"

    print("[PASS] Optimization via analysis_id succeeded and cross-session security (IDOR prevention) verified.")


if __name__ == "__main__":
    test_target_range_validation()
    test_intermediate_representation_and_non_fabrication()
    test_role_fallback_neutrality()
    test_target_achievement_with_supported_evidence()
    test_fastapi_endpoints_and_session_isolation()
    test_optimization_via_analysis_id_and_cross_session_security()
    print("\n=======================================================")
    print("ALL OPTIMIZER & SECURITY TESTS PASSED (100% SUCCESS)!")
    print("=======================================================\n")
