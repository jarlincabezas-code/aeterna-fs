from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime


def generate_audit_report(output_path: str, data: dict):
    """
    Aeterna – Professional Integrity Audit Report
    Cryptographic Integrity & Audit Assurance Report
    """

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    # -----------------------------
    # Title
    # -----------------------------
    title_style = ParagraphStyle(
        "TitleStyle",
        fontSize=18,
        spaceAfter=12,
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        fontSize=10,
        spaceAfter=24,
        alignment=1,
        textColor=colors.grey
    )

    story.append(Paragraph("AETERNA – INTEGRITY AUDIT REPORT", title_style))
    story.append(Paragraph(
        "Cryptographic Integrity & Audit Assurance Report",
        subtitle_style
    ))

    # -----------------------------
    # Executive Summary
    # -----------------------------
    story.append(Paragraph("Executive Summary", styles["Heading2"]))

    summary_text = (
        f"This report documents the deterministic integrity verification performed by "
        f"<b>Aeterna</b> on <b>{data.get('verified_at')}</b>.<br/><br/>"
        f"Aeterna evaluated the complete sequence of recorded operational events using "
        f"cryptographically chained audit records.<br/><br/>"
        f"<b>VERDICT: {data.get('verdict')}</b><br/><br/>"
        f"No evidence of post-ingest modification, record tampering, record deletion, "
        f"or chain discontinuity was detected within the evaluated scope at the time of verification."
    )

    story.append(Paragraph(summary_text, styles["BodyText"]))
    story.append(Spacer(1, 16))

    # -----------------------------
    # System Identification
    # -----------------------------
    story.append(Paragraph("System Identification", styles["Heading2"]))

    system_table = Table([
        ["Instance ID", data.get("instance_id")],
        ["Customer", data.get("customer")],
        ["License Type", data.get("license_type")],
        ["Declared Scope", data.get("scope")]
    ], colWidths=[160, 320])

    system_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    story.append(system_table)
    story.append(Spacer(1, 16))

    # -----------------------------
    # Verification Details
    # -----------------------------
    story.append(Paragraph("Verification Details", styles["Heading2"]))

    verification_text = (
        f"A total of <b>{data.get('checked_events')}</b> sequentially chained audit records "
        f"were verified, forming a continuous integrity chain from session initiation "
        f"through session closure.<br/><br/>"
        f"The verification process is deterministic: any alteration, removal, or insertion "
        f"of records after ingestion would irreversibly break the chain and be immediately detectable."
    )

    story.append(Paragraph(verification_text, styles["BodyText"]))
    story.append(Spacer(1, 16))

    # -----------------------------
    # Scope Monitoring
    # -----------------------------
    story.append(Paragraph("Scope Monitoring and Control", styles["Heading2"]))

    scope_text = (
        "During operation, Aeterna continuously monitored execution activity against the "
        "declared operational scope.<br/><br/>"
        "<b>No scope violations, unauthorized execution paths, or integrity anomalies "
        "were detected during the monitored period.</b>"
    )

    story.append(Paragraph(scope_text, styles["BodyText"]))
    story.append(Spacer(1, 16))

    # -----------------------------
    # Technical Assurance
    # -----------------------------
    story.append(Paragraph("Technical Assurance", styles["Heading2"]))

    technical_text = (
        "Aeterna implements cryptographically chained audit records using "
        "<b>SHA3-512 hashing</b>, combined with <b>HMAC-based digital signature generation "
        "at ingestion time</b>.<br/><br/>"
        "Each record’s integrity depends on the immutability of all preceding records. "
        "Any post-ingest modification invalidates all subsequent records and compromises "
        "the audit chain in a deterministic and non-repudiable manner.<br/><br/>"
        "This report attests exclusively to <b>data integrity over time</b>. It does not "
        "assert the correctness, legality, or semantic validity of the underlying data itself."
    )

    story.append(Paragraph(technical_text, styles["BodyText"]))
    story.append(Spacer(1, 16))

    # -----------------------------
    # Deliverable Evidence Record
    # -----------------------------
    story.append(Paragraph("Deliverable Evidence Record", styles["Heading2"]))

    # Estilo monoespaciado con wrapping correcto
    hash_style = ParagraphStyle(
    "HashStyle",
    fontName="Courier",
    fontSize=8,
    leading=10,
    wordWrap="CJK"   # Permite que hashes largos se ajusten en la celda
  )

    deliverable_hash = data.get("deliverable_hash", "N/A")

    deliverable_table = Table([
    ["Deliverable Hash", Paragraph(deliverable_hash, hash_style)],
    ["Hash Algorithm", data.get("deliverable_hash_algorithm", "SHA3-512")],
    ["Declared By", data.get("deliverable_declared_by", "N/A")],
    ["Purpose", data.get("deliverable_purpose", "N/A")]
], colWidths=[160, 320])

    deliverable_table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
]))

    story.append(deliverable_table)
    story.append(Spacer(1, 16))


    # -----------------------------
    # Evidence Integrity Statement
    # -----------------------------
    story.append(Paragraph("Evidence Integrity Statement", styles["Heading2"]))

    evidence_text = (
        "This document constitutes a <b>deterministic integrity artifact</b> derived exclusively "
        "from cryptographically verifiable audit records.<br/><br/>"
        "Any modification to the underlying records after the reported verification timestamp "
        "is cryptographically detectable and invalidates both the audit chain and this report."
    )

    story.append(Paragraph(evidence_text, styles["BodyText"]))
    story.append(Spacer(1, 16))

    # -----------------------------
    # Instance Binding
    # -----------------------------
    story.append(Paragraph("Instance Binding", styles["Heading2"]))

    binding_text = (
        "This report is cryptographically bound to a specific Aeterna execution instance. "
        "The following fingerprint uniquely identifies the audited system instance at the "
        "time of verification:"
    )

    story.append(Paragraph(binding_text, styles["BodyText"]))
    story.append(Spacer(1, 8))

    fingerprint_table = Table([
        ["Instance Fingerprint", data.get("instance_fingerprint")]
    ], colWidths=[200, 280])

    fingerprint_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, 0), colors.whitesmoke),
        ("FONT", (1, 0), (1, 0), "Courier")
    ]))

    story.append(fingerprint_table)
    story.append(Spacer(1, 16))

    # -----------------------------
    # Sealed Deliverable
    # -----------------------------
    story.append(Paragraph("Sealed Deliverable", styles["Heading2"]))

    deliverable_table = Table([
    ["Deliverable Hash (SHA3-512)", Paragraph(data.get("deliverable_hash", "N/A"), hash_style)],
    ["Declared By", Paragraph(data.get("deliverable_declared_by", "N/A"), styles["BodyText"])],
    ["Purpose", Paragraph(data.get("deliverable_purpose", "N/A"), styles["BodyText"])]
], colWidths=[200, 280])


    deliverable_table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
    ("FONT", (1, 0), (1, 0), "Courier"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
]))
    
    story.append(deliverable_table)
    story.append(Spacer(1, 16))


    # -----------------------------
    # Cryptographic Attestation
    # -----------------------------
    story.append(Paragraph("Cryptographic Attestation & Non-Repudiation", styles["Heading2"]))

    mono = ParagraphStyle(
        "Mono",
        fontName="Courier",
        fontSize=9,
        spaceAfter=10
    )

    story.append(Paragraph(
        f"<b>Report Hash (SHA3-512)</b><br/>{data.get('report_hash')}",
        mono
    ))

    story.append(Paragraph(
        f"<b>Digital Signature (HMAC – Aeterna)</b><br/>{data.get('report_signature')}",
        mono
    ))

    # -----------------------------
    # Footer
    # -----------------------------
    footer = Paragraph(
        f"Report generated by <b>Aeterna</b><br/>"
        f"{datetime.utcnow().isoformat()} UTC<br/><br/>"
        f"Confidential – Generated for internal audit, compliance, and executive review",
        styles["Italic"]
    )

    story.append(Spacer(1, 32))
    story.append(footer)

    doc.build(story)
