import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.optimizer import (
    optimize_resume,
    validate_target_range,
    TargetRangeValidationError,
    parse_resume_text,
    ResumeDocument,
)
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class Phase3AuditTestSuite(unittest.TestCase):

    def test_01_target_range_edge_cases(self):
        """Audit target range validation with all required edge cases."""
        # Valid edge cases
        self.assertEqual(validate_target_range(0, 5), (0, 5))
        self.assertEqual(validate_target_range(5, 10), (5, 10))
        self.assertEqual(validate_target_range(75, 80), (75, 80))
        self.assertEqual(validate_target_range(80, 85), (80, 85))
        self.assertEqual(validate_target_range(85, 90), (85, 90))
        self.assertEqual(validate_target_range(95, 100), (95, 100))

        # Invalid edge cases (must raise TargetRangeValidationError)
        with self.assertRaises(TargetRangeValidationError):
            validate_target_range(100, 100)

        with self.assertRaises(TargetRangeValidationError):
            validate_target_range(85, 80)

        with self.assertRaises(TargetRangeValidationError):
            validate_target_range(-5, 80)

        with self.assertRaises(TargetRangeValidationError):
            validate_target_range(80, 105)

        with self.assertRaises(TargetRangeValidationError):
            validate_target_range(80, 82)  # span < 5

    def test_02_section_preservation_and_non_ascii(self):
        """Audit that all sections, custom headers, and non-ASCII characters are preserved."""
        complex_resume = """Alex Mercer | alex.mercer@example.com | +1-555-0199 | San Francisco, CA

Professional Summary
Experienced Software Engineer with a passion for building resilient backend microservices and distributed systems.

Technical Skills
Python, PostgreSQL, Docker, FastAPI, Redis, Git, Linux

Professional Experience
Senior Backend Engineer | TechCorp Inc. (2021 – Present)
- Architected asynchronous REST APIs in Python and FastAPI handling 10k req/sec.
- Optimized PostgreSQL queries and reduced p99 latency by 45%.
- Implemented Docker CI/CD pipelines with automated testing.

Software Engineer | StartupLabs (2019 – 2021)
- Developed data pipelines using Python and Redis.
- Collaborated with frontend engineers on REST API schemas.

Technical Projects
Cloud Distributed Lock Manager (Python & Redis)
- Built distributed locking mechanism using Redis redlock algorithm.
- Deployed via Docker with 99.99% test coverage.

Education
B.S. in Computer Science | University of California, Berkeley (2015 – 2019)

Certifications
- AWS Certified Solutions Architect – Associate
- Certified Kubernetes Administrator (CKA)

Awards & Honors
- ACM ICPC Regional Finalist (2018)
- TechCorp Engineering Excellence Award (2023)

Publications
- Mercer, A. "High-Throughput Asynchronous Task Queues in Modern Python." PyCon Proceedings, 2022.

Volunteer Experience
- Volunteer Python Instructor at Code For All (2020 – Present)

Languages
- English (Native), Spanish (Professional proficiency), French (Conversational)
"""
        doc = parse_resume_text(complex_resume)
        rendered = doc.render_text()

        # Verify all sections exist in the rendered output
        self.assertIn("Professional Summary", rendered)
        self.assertIn("Technical Skills", rendered)
        self.assertIn("Professional Experience", rendered)
        self.assertIn("Projects", rendered)
        self.assertIn("Education", rendered)
        self.assertIn("Certifications", rendered)
        self.assertIn("AWS Certified Solutions Architect", rendered)
        self.assertIn("Awards", rendered)
        self.assertIn("ACM ICPC Regional Finalist", rendered)
        self.assertIn("Publications", rendered)
        self.assertIn("PyCon Proceedings", rendered)
        self.assertIn("Volunteer", rendered)
        self.assertIn("Languages", rendered)

        # Run optimizer and ensure all sections are preserved in final_resume_text
        jd = "Seeking a Senior Backend Engineer proficient in Python, FastAPI, PostgreSQL, Docker, and Redis."
        res = optimize_resume(complex_resume, jd, 80, 85)
        self.assertIn("Awards", res.final_resume_text)
        self.assertIn("Publications", res.final_resume_text)
        self.assertIn("Volunteer", res.final_resume_text)
        self.assertIn("Languages", res.final_resume_text)
        self.assertIn("Certifications", res.final_resume_text)

    def test_03_contract_fidelity_and_non_fabrication(self):
        """Audit that the API response strictly matches the frontend contract."""
        session_cookie = f"ai_resume_session_{uuid.uuid4()}"
        headers = {"Cookie": f"session_id={session_cookie}"}

        jd = "We need an expert in Python, FastAPI, PostgreSQL, Kubernetes, C++, Rust, Hadoop, Spark, Swift, Flutter, AWS, and GCP."

        # Test direct optimizer call to verify contract
        res = optimize_resume("Alex Mercer\nPython, PostgreSQL, FastAPI\nExperience\nSoftware Engineer\n- Developed in Python", jd, 80, 85)
        data = res.to_dict()

        # Field-by-field contract audit
        required_fields = [
            "optimization_id",
            "original_score",
            "target_min",
            "target_max",
            "final_score",
            "target_achieved",
            "iteration_count",
            "original_resume_text",
            "final_resume_text",
            "unsupported_requirements",
            "supported_requirements",
            "changes",
            "iterations",
            "optimization_summary",
        ]
        for field in required_fields:
            self.assertIn(field, data, f"Missing contract field: {field}")

        # Verify numeric types
        self.assertIsInstance(data["original_score"], (int, float))
        self.assertIsInstance(data["final_score"], (int, float))
        self.assertIsInstance(data["target_min"], int)
        self.assertIsInstance(data["target_max"], int)
        self.assertIsInstance(data["target_achieved"], bool)

        # Non-fabrication check: missing skills like C++, Rust, Swift MUST be in unsupported_requirements
        self.assertTrue(any("c++" in s.lower() or "rust" in s.lower() or "swift" in s.lower() for s in data["unsupported_requirements"]))

        # When target not reached, best_achievable_explanation must be a clear explanation
        if not data["target_achieved"]:
            self.assertIsNotNone(data["best_achievable_explanation"])
            self.assertIn("could not safely be reached without fabricating", data["best_achievable_explanation"])


if __name__ == "__main__":
    unittest.main()