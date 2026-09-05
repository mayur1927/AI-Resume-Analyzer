"""FastAPI application: upload, analyse, save, and download resume reports.

Optimized for both local development and Vercel/serverless cloud deployment.
"""

import io
import os
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from pypdf import PdfReader
from sqlalchemy.orm import Session

from .analyzer import analyze_resume
from .database import get_db, init_db
from .models import Analysis
from .report_generator import generate_pdf_report

MAX_FILE_SIZE_MB = 2
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024  # 2 MB (strictly within Vercel's 4.5 MB request payload limit)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan context manager for database initialization."""
    init_db()
    yield


app = FastAPI(
    title="AI Resume Analyzer API",
    description="Intelligent Resume Analysis & Job Compatibility Assessment API",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS with dynamic environment variable support and Vercel preview regex
configured_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8501",
]
allowed_origins: List[str] = list(set(default_origins + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_pdf(contents: bytes) -> str:
    """Extract plain text from binary PDF stream with format and readability validation."""
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format: The uploaded file is missing the standard PDF file signature (%PDF-).",
        )

    try:
        reader = PdfReader(io.BytesIO(contents))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password-protected PDF detected: Please upload an unencrypted, text-searchable PDF resume.",
                )
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unreadable PDF: The document appears to be corrupted or malformed and could not be parsed.",
        ) from exc

    if len(text) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Insufficient text extracted: Scanned or image-only PDFs without an embedded text layer "
                "cannot be parsed without OCR. Please upload a digital, text-searchable PDF resume."
            ),
        )
    return text


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint for container orchestrators and status monitors."""
    return {
        "status": "ok",
        "service": "ai-resume-analyzer-api",
        "version": "1.0.0",
        "max_upload_size_mb": MAX_FILE_SIZE_MB,
    }


@app.post("/api/analyze")
@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(..., min_length=30),
    db: Session = Depends(get_db),
):
    """Analyze a candidate resume against a target job description."""
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type: Please upload a PDF document (.pdf). Non-PDF files are not supported.",
        )

    contents = await resume.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: The uploaded PDF is {(len(contents) / (1024 * 1024)):.2f} MB, which exceeds the {MAX_FILE_SIZE_MB} MB limit.",
        )

    resume_text = read_pdf(contents)
    result = analyze_resume(resume_text, job_description)

    # Persist the evaluation record to PostgreSQL
    try:
        record = Analysis(
            filename=resume.filename,
            ats_score=result.ats_score,
            resume_skills=result.resume_skills,
            job_skills=result.job_skills,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            suggestions=result.suggestions,
            resume_text=resume_text,
            job_description=job_description,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        analysis_id = str(record.id)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record analysis to the database: {str(exc)}",
        ) from exc

    response_data = result.to_dict()
    response_data.update({
        "analysis_id": analysis_id,
        "filename": record.filename,
    })
    return response_data


@app.get("/api/analyses")
@app.get("/analyses")
def list_analyses(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List recent resume evaluations stored in PostgreSQL."""
    limit = max(1, min(limit, 50))
    records = (
        db.query(Analysis)
        .order_by(Analysis.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "analysis_id": str(r.id),
            "filename": r.filename,
            "ats_score": r.ats_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "matched_skills_count": len(r.matched_skills or []),
            "missing_skills_count": len(r.missing_skills or []),
            "matched_skills": r.matched_skills or [],
        }
        for r in records
    ]


@app.get("/api/analyses/{analysis_id}")
@app.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve an existing analysis by UUID."""
    record = db.get(Analysis, analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found.",
        )

    breakdown = None
    if record.resume_text and record.job_description:
        try:
            breakdown = analyze_resume(record.resume_text, record.job_description).score_breakdown
        except Exception:
            breakdown = None

    if not breakdown:
        breakdown = {
            "skill_match": int(round(record.ats_score * 0.6)),
            "keyword_match": int(round(record.ats_score * 0.2)),
            "sections": int(round(record.ats_score * 0.1)),
            "formatting": int(round(record.ats_score * 0.1)),
        }

    return {
        "analysis_id": str(record.id),
        "filename": record.filename,
        "ats_score": record.ats_score,
        "score_breakdown": breakdown,
        "resume_skills": record.resume_skills or [],
        "job_skills": record.job_skills or [],
        "matched_skills": record.matched_skills or [],
        "missing_skills": record.missing_skills or [],
        "suggestions": record.suggestions or [],
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@app.get("/api/analyses/{analysis_id}/report")
@app.get("/analyses/{analysis_id}/report")
def download_report(
    analysis_id: uuid.UUID,
    format: str = "pdf",
    db: Session = Depends(get_db),
):
    """Export and download a formatted PDF or plaintext evaluation report for an analysis."""
    record = db.get(Analysis, analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found.",
        )

    # Optional plain text format export
    if format.lower() == "txt":
        matched = ", ".join(record.matched_skills) if record.matched_skills else "No matched skills found"
        missing = ", ".join(record.missing_skills) if record.missing_skills else "No missing skills identified"
        suggestions_text = "\n".join(f"- {s}" for s in record.suggestions)

        report = f"""============================================================
AI RESUME ANALYZER - CANDIDATE EVALUATION REPORT
Intelligent Resume Analysis & Job Compatibility Assessment
============================================================

Resume Document: {record.filename}
Evaluation Date: {record.created_at}
ATS Match Score: {record.ats_score}/100 PTS

------------------------------------------------------------
1. VERIFIED MATCHED COMPETENCIES
------------------------------------------------------------
{matched}

------------------------------------------------------------
2. MISSING / UNMATCHED JOB SKILLS
------------------------------------------------------------
{missing}

------------------------------------------------------------
3. ACTIONABLE RECOMMENDATIONS & OPTIMIZATION TIPS
------------------------------------------------------------
{suggestions_text}

============================================================
Report Generated by AI Resume Analyzer (v1.0)
============================================================
"""
        return PlainTextResponse(
            report,
            headers={
                "Content-Disposition": f'attachment; filename="resume-analysis-{analysis_id}.txt"'
            },
        )

    # Default: Professional Print-Ready PDF Report
    breakdown = None
    if record.resume_text and record.job_description:
        try:
            breakdown = analyze_resume(record.resume_text, record.job_description).score_breakdown
        except Exception:
            breakdown = None

    pdf_bytes = generate_pdf_report(
        filename=record.filename,
        ats_score=record.ats_score,
        score_breakdown=breakdown,
        matched_skills=record.matched_skills or [],
        missing_skills=record.missing_skills or [],
        resume_skills=record.resume_skills or [],
        suggestions=record.suggestions or [],
        created_at=record.created_at,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="resume-analysis-{analysis_id}.pdf"'
        },
    )
