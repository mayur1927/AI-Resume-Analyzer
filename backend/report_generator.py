"""Professional PDF Evaluation Report Generator using ReportLab.

Generates an executive, print-ready PDF evaluation summary for candidate resumes.
"""

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf_report(
    filename: str,
    ats_score: float,
    score_breakdown: Optional[Dict[str, int]],
    matched_skills: List[str],
    missing_skills: List[str],
    resume_skills: List[str],
    suggestions: List[str],
    created_at: Optional[datetime] = None,
) -> bytes:
    """Generate a high-quality, professional PDF report as binary bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    bold_label = ParagraphStyle(
        "BoldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
    )
    suggestion_item = ParagraphStyle(
        "SuggestionItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        firstLineIndent=-12,
        spaceAfter=4,
    )
    tag_matched = ParagraphStyle(
        "TagMatched",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#065f46"),
    )
    tag_missing = ParagraphStyle(
        "TagMissing",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#92400e"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("AI Resume Analyzer", title_style))
    story.append(
        Paragraph(
            "Intelligent Resume Analysis & Job Compatibility Assessment Report",
            subtitle_style,
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2563eb"),
            spaceBefore=0,
            spaceAfter=12,
        )
    )

    # 2. Metadata Information Table
    date_str = (
        created_at.strftime("%B %d, %Y at %H:%M UTC")
        if created_at
        else datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
    )
    meta_data = [
        [
            Paragraph("Target Resume:", bold_label),
            Paragraph(filename, body_style),
            Paragraph("Evaluation Date:", bold_label),
            Paragraph(date_str, body_style),
        ],
        [
            Paragraph("Evaluation Engine:", bold_label),
            Paragraph("spaCy Deterministic Matcher", body_style),
            Paragraph("Assessment Type:", bold_label),
            Paragraph("4-Tier ATS Compatibility", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[90, 180, 100, 160])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Score Hero & Breakdown Table
    breakdown = score_breakdown or {"skill_match": 0, "keyword_match": 0, "sections": 0, "formatting": 0}
    
    score_int = int(round(ats_score))
    if score_int >= 80:
        score_badge = "Strong ATS Alignment"
        badge_bg = colors.HexColor("#dcfce7")
        badge_fg = colors.HexColor("#15803d")
    elif score_int >= 65:
        score_badge = "Moderate ATS Alignment"
        badge_bg = colors.HexColor("#dbeafe")
        badge_fg = colors.HexColor("#1d4ed8")
    elif score_int >= 50:
        score_badge = "Average Alignment"
        badge_bg = colors.HexColor("#fef3c7")
        badge_fg = colors.HexColor("#b45309")
    else:
        score_badge = "Low Alignment / Review Needed"
        badge_bg = colors.HexColor("#ffe4e6")
        badge_fg = colors.HexColor("#be123c")

    score_card_data = [
        [
            Paragraph(
                f"<font size=28 color='#0f172a'><b>{score_int}</b></font><font size=12 color='#64748b'> / 100</font><br/><font size=9 color='{badge_fg.hexval()}'><b>{score_badge}</b></font>",
                ParagraphStyle("ScoreDisplay", alignment=1, leading=16),
            ),
            Table(
                [
                    [Paragraph("<b>Dimension</b>", bold_label), Paragraph("<b>Score</b>", bold_label), Paragraph("<b>Weight</b>", bold_label)],
                    [Paragraph("Technical Skill Match", body_style), Paragraph(f"<b>{breakdown.get('skill_match', 0)}</b> / 60", body_style), Paragraph("60%", body_style)],
                    [Paragraph("JD Keyword Alignment", body_style), Paragraph(f"<b>{breakdown.get('keyword_match', 0)}</b> / 20", body_style), Paragraph("20%", body_style)],
                    [Paragraph("Section Structure", body_style), Paragraph(f"<b>{breakdown.get('sections', 0)}</b> / 10", body_style), Paragraph("10%", body_style)],
                    [Paragraph("Contact & Formatting", body_style), Paragraph(f"<b>{breakdown.get('formatting', 0)}</b> / 10", body_style), Paragraph("10%", body_style)],
                ],
                colWidths=[150, 90, 70],
            ),
        ]
    ]
    
    score_table = Table(score_card_data, colWidths=[180, 350])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(score_table)
    story.append(Spacer(1, 14))

    # 4. Competency & Skills Matrix
    story.append(Paragraph("Competency & Skills Assessment", section_heading))
    
    matched_text = ", ".join(matched_skills) if matched_skills else "No direct matching skills detected from taxonomy."
    missing_text = ", ".join(missing_skills) if missing_skills else "None - Full coverage of all job requirements identified."
    detected_text = ", ".join(resume_skills) if resume_skills else "No technical skills recognized from vocabulary."

    skills_data = [
        [
            Paragraph("<b>Verified Matched Skills</b>", tag_matched),
            Paragraph(matched_text, body_style),
        ],
        [
            Paragraph("<b>Missing / Unmatched Skills</b>", tag_missing),
            Paragraph(missing_text, body_style),
        ],
        [
            Paragraph("<b>All Extracted Resume Skills</b>", bold_label),
            Paragraph(detected_text, body_style),
        ],
    ]
    skills_table = Table(skills_data, colWidths=[150, 380])
    skills_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#ecfdf5")),
                ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#fffbeb")),
                ("BACKGROUND", (0, 2), (0, 2), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(skills_table)
    story.append(Spacer(1, 14))

    # 5. Improvement Suggestions
    story.append(Paragraph("Actionable Optimization Recommendations", section_heading))
    if suggestions:
        for idx, item in enumerate(suggestions, 1):
            story.append(Paragraph(f"<b>{idx}.</b> {item}", suggestion_item))
    else:
        story.append(
            Paragraph(
                "• Strong alignment across all evaluation dimensions. Tailor executive summaries to specific employer needs before submitting.",
                body_style,
            )
        )

    story.append(Spacer(1, 16))
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#cbd5e1"),
            spaceBefore=0,
            spaceAfter=8,
        )
    )
    story.append(
        Paragraph(
            "<font color='#94a3b8' size=8>This report was automatically compiled by the AI Resume Analyzer NLP evaluation engine. Metrics and heuristics provide guidance for resume enhancement and do not constitute hiring decisions.</font>",
            ParagraphStyle("FooterNotice", alignment=1),
        )
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
