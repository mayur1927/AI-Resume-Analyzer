"""End-to-End local test runner for AI Resume Analyzer.

Validates:
1. Valid resume analysis
2. Invalid file rejection
3. Oversized file (>2 MB) rejection
4. Empty/short job description rejection
5. Resume with matching skills
6. Resume with missing skills
7. Resume with poor formatting (missing sections, missing email)
8. Resume containing no extractable text (<50 characters)
9. Health endpoint
10. Database persistence & retrieval
11. Professional PDF report generation
"""

import io
import os
import sys
import unittest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app, MAX_FILE_SIZE
from backend.database import init_db


def create_pdf(text_lines, pad_bytes=0) -> bytes:
    """Helper to generate in-memory PDF binary with specified text lines and optional padding."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in text_lines:
        p.drawString(50, y, line)
        y -= 20
    p.save()
    pdf_bytes = buffer.getvalue()
    if pad_bytes > 0:
        pdf_bytes += b" " * pad_bytes
    return pdf_bytes


class LocalE2ETestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Verify /health and /api/health return 200 OK and expected metadata."""
        for path in ["/health", "/api/health"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["service"], "ai-resume-analyzer-api")
            self.assertEqual(data["max_upload_size_mb"], 2)

    def test_02_valid_resume_analysis(self):
        """Test Case 1: Valid resume against target JD."""
        resume_lines = [
            "Jane Doe - Software Engineer",
            "Email: jane.doe@example.com | Phone: (555) 123-4567 | San Francisco, CA",
            "Summary: Results-oriented Full Stack Engineer with 4+ years of experience building scalable web services.",
            "Experience:",
            "Senior Backend Engineer at TechCorp (2022 - Present)",
            "- Developed and deployed microservices using Python, FastAPI, and PostgreSQL.",
            "- Containerized applications using Docker and orchestrated CI/CD pipelines in Git.",
            "- Improved database query execution time by 40% using Redis caching.",
            "Projects:",
            "- Cloud Analytics Dashboard: Built full-stack system using React, TypeScript, and FastAPI.",
            "Skills:",
            "Python, FastAPI, Docker, PostgreSQL, React, TypeScript, Git, Redis, Linux, Unit Testing, SQL",
            "Education:",
            "B.S. in Computer Science - University of California (2020)",
        ]
        pdf_bytes = create_pdf(resume_lines)

        jd = (
            "We are seeking a Python & React Full Stack Engineer. "
            "The candidate must be proficient in Python, FastAPI, React, TypeScript, Docker, and PostgreSQL. "
            "Experience with Git, Redis, and writing unit tests is highly desirable."
        )

        response = self.client.post(
            "/api/analyze",
            files={"resume": ("jane_doe_resume.pdf", pdf_bytes, "application/pdf")},
            data={"job_description": jd},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("analysis_id", data)
        self.assertIn("ats_score", data)
        self.assertGreaterEqual(data["ats_score"], 70)
        self.assertIn("python", [s.lower() for s in data["matched_skills"]])
        self.assertIn("fastapi", [s.lower() for s in data["matched_skills"]])
        self.assertIn("docker", [s.lower() for s in data["matched_skills"]])
        self.assertGreater(data["score_breakdown"]["skill_match"], 40)
        self.assertGreaterEqual(data["score_breakdown"]["sections"], 8)
        self.assertEqual(data["score_breakdown"]["formatting"], 10)

        # Verify Analysis Retrieval by ID
        analysis_id = data["analysis_id"]
        get_res = self.client.get(f"/api/analyses/{analysis_id}")
        self.assertEqual(get_res.status_code, 200)
        retrieved = get_res.json()
        self.assertEqual(retrieved["analysis_id"], analysis_id)
        self.assertEqual(retrieved["filename"], "jane_doe_resume.pdf")

        # Verify PDF Report Generation
        report_res = self.client.get(f"/api/analyses/{analysis_id}/report")
        self.assertEqual(report_res.status_code, 200)
        self.assertEqual(report_res.headers["content-type"], "application/pdf")
        self.assertTrue(report_res.content.startswith(b"%PDF-"))

        # Verify Plaintext Report Generation
        txt_res = self.client.get(f"/api/analyses/{analysis_id}/report?format=txt")
        self.assertEqual(txt_res.status_code, 200)
        self.assertIn("AI RESUME ANALYZER", txt_res.text)

    def test_03_invalid_file_rejection(self):
        """Test Case 2: Reject non-PDF or corrupted binary files."""
        # Case 2a: Non-pdf extension
        res1 = self.client.post(
            "/api/analyze",
            files={"resume": ("resume.txt", b"Just some plain text content", "text/plain")},
            data={"job_description": "We need a software engineer with Python and SQL experience."},
        )
        self.assertEqual(res1.status_code, 400)
        self.assertIn("Invalid file type", res1.json()["detail"])

        # Case 2b: .pdf extension but invalid header (no %PDF-)
        res2 = self.client.post(
            "/api/analyze",
            files={"resume": ("fake.pdf", b"NOT A REAL PDF FILE HEADER", "application/pdf")},
            data={"job_description": "We need a software engineer with Python and SQL experience."},
        )
        self.assertEqual(res2.status_code, 400)
        self.assertIn("missing the standard PDF file signature", res2.json()["detail"])

    def test_04_oversized_file_rejection(self):
        """Test Case 3: Reject files exceeding 2 MB limit."""
        # Create a valid PDF padded to 2.2 MB
        valid_pdf = create_pdf(["Small text line"], pad_bytes=int(2.2 * 1024 * 1024))
        self.assertGreater(len(valid_pdf), MAX_FILE_SIZE)

        res = self.client.post(
            "/api/analyze",
            files={"resume": ("large_resume.pdf", valid_pdf, "application/pdf")},
            data={"job_description": "We need a software engineer with Python and SQL experience."},
        )
        self.assertEqual(res.status_code, 413)
        self.assertIn("File too large", res.json()["detail"])

    def test_05_empty_or_short_job_description(self):
        """Test Case 4: Reject empty or excessively short job descriptions (< 30 chars)."""
        valid_pdf = create_pdf([
            "Jane Doe - Software Engineer",
            "Email: jane@example.com",
            "Experience: Python and SQL developer",
            "Skills: Python, SQL",
            "Education: BS CS",
            "Projects: API project",
            "Summary: Software Developer",
        ])

        # Short JD
        res1 = self.client.post(
            "/api/analyze",
            files={"resume": ("resume.pdf", valid_pdf, "application/pdf")},
            data={"job_description": "Too short"},
        )
        self.assertEqual(res1.status_code, 422)

        # Empty JD
        res2 = self.client.post(
            "/api/analyze",
            files={"resume": ("resume.pdf", valid_pdf, "application/pdf")},
            data={"job_description": ""},
        )
        self.assertEqual(res2.status_code, 422)

    def test_06_resume_with_matching_skills(self):
        """Test Case 5: High match rate when resume heavily aligns with JD."""
        resume_lines = [
            "Alex Smith - Senior Python Engineer",
            "Email: alex.smith@example.com | Phone: 123-456-7890",
            "Summary: Senior Software Engineer specializing in Python, FastAPI, Docker, and PostgreSQL.",
            "Experience:",
            "- Architected microservices with FastAPI and PostgreSQL.",
            "- Managed Kubernetes clusters and Docker containers in AWS.",
            "- Implemented automated unit testing with pytest and configured CI/CD pipelines.",
            "Projects:",
            "- Data Ingestion Service: Scaled to 50k req/sec with Redis and Kafka.",
            "Skills:",
            "Python, FastAPI, Docker, Kubernetes, PostgreSQL, AWS, CI/CD, Pytest, Redis, Kafka, Git, Linux",
            "Education:",
            "Master of Science in Software Engineering",
        ]
        pdf_bytes = create_pdf(resume_lines)

        jd = (
            "Looking for a Senior Python Developer with deep experience in FastAPI, Docker, Kubernetes, "
            "PostgreSQL, AWS, CI/CD, and Redis. Must be capable of building distributed microservices."
        )

        res = self.client.post(
            "/api/analyze",
            files={"resume": ("alex_python_sr.pdf", pdf_bytes, "application/pdf")},
            data={"job_description": jd},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertGreaterEqual(data["ats_score"], 80)
        self.assertGreaterEqual(len(data["matched_skills"]), 5)
        self.assertEqual(len(data["missing_skills"]), 0)
        self.assertEqual(data["score_breakdown"]["skill_match"], 60)

    def test_07_resume_with_missing_skills(self):
        """Test Case 6: Detect skill gaps when candidate skills don't match target JD."""
        resume_lines = [
            "Taylor Designer - UI/UX Specialist",
            "Email: taylor.ux@example.com | Portfolio: taylor-designs.io",
            "Summary: Creative designer experienced in user research, wireframing, and interactive design.",
            "Experience:",
            "- Designed web and mobile applications using Figma and Adobe Creative Suite.",
            "- Conducted usability tests and user interviews across 10+ projects.",
            "Projects:",
            "- E-commerce Mobile UI redesign in Figma.",
            "Skills:",
            "Figma, Agile, Communication",
            "Education:",
            "B.A. in Graphic Design",
        ]
        pdf_bytes = create_pdf(resume_lines)

        jd = (
            "Senior Machine Learning Engineer required. "
            "Must have extensive experience with PyTorch, TensorFlow, Python, Docker, Kubernetes, "
            "Scikit-Learn, Pandas, NumPy, and Natural Language Processing."
        )

        res = self.client.post(
            "/api/analyze",
            files={"resume": ("taylor_ux.pdf", pdf_bytes, "application/pdf")},
            data={"job_description": jd},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Skill match score should be very low since Figma/Agile do not match ML skills
        self.assertLessEqual(data["score_breakdown"]["skill_match"], 10)
        self.assertGreaterEqual(len(data["missing_skills"]), 5)
        # Suggestions should include skill alignment recommendations
        suggestions_str = " ".join(data["suggestions"])
        self.assertIn("Technical Skill Alignment", suggestions_str)

    def test_08_resume_with_poor_formatting(self):
        """Test Case 7: Unstructured text dump lacking standard sections and contact info."""
        poor_lines = [
            "I worked at a company doing some coding and fixing bugs for customers.",
            "I wrote some python code and worked with sql databases on several tasks.",
            "I also learned how to use docker containers and git repositories during my time there.",
            "I like programming and building applications on linux servers.",
            "I am looking for a developer job where I can continue learning software engineering.",
        ]
        pdf_bytes = create_pdf(poor_lines)

        jd = "Seeking a Software Developer with experience in Python, SQL, Docker, Git, and Linux."

        res = self.client.post(
            "/api/analyze",
            files={"resume": ("unstructured_resume.pdf", pdf_bytes, "application/pdf")},
            data={"job_description": jd},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Section score and format score should reflect missing headers and missing email
        self.assertLessEqual(data["score_breakdown"]["sections"], 4)
        self.assertEqual(data["score_breakdown"]["formatting"], 5)  # Has sensible length but no email
        suggestions_str = " ".join(data["suggestions"])
        self.assertIn("Contact Information", suggestions_str)
        self.assertIn("Resume Structure", suggestions_str)

    def test_09_resume_with_no_extractable_text(self):
        """Test Case 8: Scanned/image-only or blank PDF with < 50 characters of text."""
        # PDF with almost no text
        blank_pdf = create_pdf(["Hi"])

        jd = "Looking for a software engineer proficient in Python and React."

        res = self.client.post(
            "/api/analyze",
            files={"resume": ("blank_scanned.pdf", blank_pdf, "application/pdf")},
            data={"job_description": jd},
        )
        self.assertEqual(res.status_code, 422)
        self.assertIn("Insufficient text extracted", res.json()["detail"])

    def test_10_history_list_endpoint(self):
        """Verify /api/analyses returns recent evaluations from PostgreSQL."""
        res = self.client.get("/api/analyses?limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("analysis_id", first)
        self.assertIn("filename", first)
        self.assertIn("ats_score", first)
        self.assertIn("created_at", first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
