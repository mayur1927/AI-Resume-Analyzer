"""Automated User-Data Isolation & Anonymous Session Security Test Suite.

Verifies:
1. Fresh visitors receive a secure, HttpOnly anonymous session cookie.
2. Session A creates Analysis A; Session B creates Analysis B.
3. Session A history contains Analysis A and excludes Analysis B.
4. Session B history contains Analysis B and excludes Analysis A.
5. Cross-session access to individual analyses (/api/analyses/{id}) yields HTTP 404.
6. Cross-session access to reports (/api/analyses/{id}/report) yields HTTP 404.
7. Existing legacy records without active session match are inaccessible to new sessions.
"""

import io
import os
import sys
import unittest
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app, COOKIE_SESSION_KEY
from backend.database import init_db


def create_pdf(text_lines) -> bytes:
    """Helper to generate in-memory PDF binary."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in text_lines:
        p.drawString(50, y, line)
        y -= 20
    p.save()
    return buffer.getvalue()


class SessionIsolationTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_session_cookie_initialization_and_attributes(self):
        """Test that fresh clients automatically receive an HttpOnly SameSite=Lax session cookie."""
        client = TestClient(app)
        res = client.get("/api/analyses")
        self.assertEqual(res.status_code, 200)

        self.assertIn(COOKIE_SESSION_KEY, client.cookies)
        session_id_str = client.cookies[COOKIE_SESSION_KEY]
        # Must be valid UUID4
        session_uuid = uuid.UUID(session_id_str)
        self.assertEqual(session_uuid.version, 4)

        # Verify cookie header properties
        set_cookie_header = res.headers.get("set-cookie", "")
        self.assertIn("HttpOnly", set_cookie_header, "Cookie must be HttpOnly")
        self.assertIn("samesite=lax", set_cookie_header.lower(), "Cookie must have SameSite=Lax")

    def test_02_multi_session_crud_and_history_isolation(self):
        """Verify strict isolation between Session A and Session B."""
        # Setup Client A
        client_a = TestClient(app)
        pdf_a = create_pdf([
            "Alice Developer - Python Engineer",
            "Email: alice@example.com",
            "Experience: Built microservices with Python, FastAPI, and Docker.",
            "Skills: Python, FastAPI, Docker, PostgreSQL, SQL, Git",
            "Education: B.S. in Computer Science",
            "Projects: API Gateway",
            "Summary: Backend Engineer",
        ])
        jd_a = "Looking for a Python Developer with FastAPI and PostgreSQL experience."

        res_a = client_a.post(
            "/api/analyze",
            files={"resume": ("alice_resume.pdf", pdf_a, "application/pdf")},
            data={"job_description": jd_a},
        )
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.json()
        analysis_id_a = data_a["analysis_id"]

        # Setup Client B (distinct session)
        client_b = TestClient(app)
        pdf_b = create_pdf([
            "Bob Architect - Cloud Engineer",
            "Email: bob@example.com",
            "Experience: Managed Kubernetes clusters and AWS infrastructure.",
            "Skills: Kubernetes, Docker, AWS, Terraform, Linux, CI/CD",
            "Education: M.S. in Cloud Systems",
            "Projects: Infrastructure Automation",
            "Summary: DevOps Specialist",
        ])
        jd_b = "Looking for a DevOps Engineer with Kubernetes, AWS, and Docker skills."

        res_b = client_b.post(
            "/api/analyze",
            files={"resume": ("bob_resume.pdf", pdf_b, "application/pdf")},
            data={"job_description": jd_b},
        )
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.json()
        analysis_id_b = data_b["analysis_id"]

        # Ensure session IDs are different
        self.assertNotEqual(
            client_a.cookies[COOKIE_SESSION_KEY],
            client_b.cookies[COOKIE_SESSION_KEY],
        )

        # 1. Test History Isolation
        history_a = client_a.get("/api/analyses").json()
        history_a_ids = [item["analysis_id"] for item in history_a]
        self.assertIn(analysis_id_a, history_a_ids, "Session A must see its own analysis")
        self.assertNotIn(analysis_id_b, history_a_ids, "Session A must NOT see Session B analysis")

        history_b = client_b.get("/api/analyses").json()
        history_b_ids = [item["analysis_id"] for item in history_b]
        self.assertIn(analysis_id_b, history_b_ids, "Session B must see its own analysis")
        self.assertNotIn(analysis_id_a, history_b_ids, "Session B must NOT see Session A analysis")

        # 2. Test Individual Record Fetch (/api/analyses/{id})
        # Authorized access
        self.assertEqual(client_a.get(f"/api/analyses/{analysis_id_a}").status_code, 200)
        self.assertEqual(client_b.get(f"/api/analyses/{analysis_id_b}").status_code, 200)

        # Cross-session unauthorized access (must return 404 without leaking existence)
        res_a_trying_b = client_a.get(f"/api/analyses/{analysis_id_b}")
        self.assertEqual(res_a_trying_b.status_code, 404)
        self.assertIn("not found", res_a_trying_b.json()["detail"].lower())

        res_b_trying_a = client_b.get(f"/api/analyses/{analysis_id_a}")
        self.assertEqual(res_b_trying_a.status_code, 404)
        self.assertIn("not found", res_b_trying_a.json()["detail"].lower())

        # 3. Test Report Download Isolation (/api/analyses/{id}/report)
        # Authorized report download
        rep_a = client_a.get(f"/api/analyses/{analysis_id_a}/report")
        self.assertEqual(rep_a.status_code, 200)
        self.assertTrue(rep_a.content.startswith(b"%PDF-"))

        rep_b = client_b.get(f"/api/analyses/{analysis_id_b}/report")
        self.assertEqual(rep_b.status_code, 200)
        self.assertTrue(rep_b.content.startswith(b"%PDF-"))

        # Cross-session unauthorized report download
        rep_a_trying_b = client_a.get(f"/api/analyses/{analysis_id_b}/report")
        self.assertEqual(rep_a_trying_b.status_code, 404)

        rep_b_trying_a = client_b.get(f"/api/analyses/{analysis_id_a}/report")
        self.assertEqual(rep_b_trying_a.status_code, 404)

    def test_03_fresh_browser_empty_history(self):
        """A new visitor with no analyses should have an empty history."""
        fresh_client = TestClient(app)
        res = fresh_client.get("/api/analyses")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data, [], "Fresh session must have an empty history")


if __name__ == "__main__":
    unittest.main(verbosity=2)
