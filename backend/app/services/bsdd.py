"""Génération du Bordereau de Suivi de Déchet Numérique (BSDD) — JSON & PDF."""
from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import settings

EMERALD = colors.HexColor("#059669")
SLATE = colors.HexColor("#1e293b")


def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, Decimal):
        return f"{v:,.2f}".replace(",", " ")
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    return str(v)


def _iso(v: datetime | None) -> str | None:
    return v.astimezone(timezone.utc).isoformat() if v else None


def build_json(tx: dict[str, Any]) -> dict[str, Any]:
    doc = {
        "document_type": "BSDD",
        "schema_version": "1.0",
        "bsdd_number": tx["bsdd_number"],
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "transaction_id": str(tx["id"]),
        "status": tx["payment_status"],
        "producer": {
            "id": str(tx["producer_id"]),
            "organization": tx["producer_organization"],
            "email": tx.get("producer_email"),
            "phone": tx["producer_phone"],
            "pickup_address": tx["address_text"],
            "coordinates": {"lat": tx["lat"], "lng": tx["lng"]},
        },
        "collector": {
            "id": str(tx["collector_id"]),
            "organization": tx["collector_organization"],
            "email": tx.get("collector_email"),
            "phone": tx["collector_phone"],
        },
        "waste": {
            "listing_id": str(tx["listing_id"]),
            "title": tx["listing_title"],
            "category": tx["category_name"],
            "category_slug": tx.get("category_slug"),
            "unit": tx["unit"],
            "agreed_quantity": str(tx["agreed_quantity"]) if tx["agreed_quantity"] is not None else None,
            "final_weight": str(tx["final_weight"]) if tx["final_weight"] is not None else None,
        },
        "financial": {
            "unit_price": str(tx["unit_price"]) if tx["unit_price"] is not None else None,
            "total_amount": str(tx["total_amount"]) if tx["total_amount"] is not None else None,
            "escrow_reference": tx["escrow_reference"],
        },
        "environmental": {
            "co2_factor_per_unit": str(tx["co2_factor_per_unit"]),
            "co2_saved_kg": str(tx["co2_saved_total"]) if tx["co2_saved_total"] is not None else None,
        },
        "traceability": {
            "reserved_at": _iso(tx["created_at"]),
            "qr_scanned_at": _iso(tx["qr_scanned_at"]),
            "collected_at": _iso(tx["collected_at"]),
            "collector_confirmed_at": _iso(tx["collector_confirmed_at"]),
            "producer_confirmed_at": _iso(tx["producer_confirmed_at"]),
            "weighing_proof_url": tx["weighing_proof_url"],
        },
    }
    # Empreinte d'intégrité (SHA-256 du contenu canonique hors date d'émission)
    canonical = json.dumps({k: v for k, v in doc.items() if k != "issued_at"}, sort_keys=True, ensure_ascii=False)
    doc["integrity_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return doc


def _qr_drawing(value: str, size: float = 32 * mm) -> Drawing:
    widget = QrCodeWidget(value)
    x1, y1, x2, y2 = widget.getBounds()
    w, h = x2 - x1, y2 - y1
    d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
    d.add(widget)
    return d


def build_pdf(tx: dict[str, Any]) -> bytes:
    data = build_json(tx)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"BSDD {tx['bsdd_number']}", author="EcoLoop Circular Hub",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=EMERALD, alignment=0, fontSize=20)
    h2 = ParagraphStyle("h2", parent=styles["Heading3"], textColor=SLATE, spaceBefore=8)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    def table(rows: list[list[str]]) -> Table:
        t = Table(rows, colWidths=[55 * mm, None])
        t.setStyle(
            TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), SLATE),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        return t

    verify_url = f"{settings.frontend_url.rstrip('/')}/transactions/{tx['id']}"
    header = Table(
        [[
            [Paragraph("Bordereau de Suivi de Déchet", h1),
             Paragraph(f"<b>N° {tx['bsdd_number']}</b> — Statut : {tx['payment_status']}", styles["Normal"]),
             Paragraph(f"Émis le {_fmt(datetime.now(timezone.utc))}", small)],
            _qr_drawing(verify_url),
        ]],
        colWidths=[None, 36 * mm],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))

    unit = tx["unit"]
    story = [
        header,
        Spacer(1, 6 * mm),
        Paragraph("1. Producteur (remettant)", h2),
        table([
            ["Organisation", _fmt(tx["producer_organization"])],
            ["Contact", f"{_fmt(tx.get('producer_email'))} / {_fmt(tx['producer_phone'])}"],
            ["Lieu d'enlèvement", _fmt(tx["address_text"])],
            ["Coordonnées GPS", f"{tx['lat']:.6f}, {tx['lng']:.6f}"],
        ]),
        Paragraph("2. Collecteur (repreneur)", h2),
        table([
            ["Organisation", _fmt(tx["collector_organization"])],
            ["Contact", f"{_fmt(tx.get('collector_email'))} / {_fmt(tx['collector_phone'])}"],
        ]),
        Paragraph("3. Déchet", h2),
        table([
            ["Lot", _fmt(tx["listing_title"])],
            ["Catégorie", _fmt(tx["category_name"])],
            ["Quantité convenue", f"{_fmt(tx['agreed_quantity'])} {unit}"],
            ["Poids réel constaté", f"{_fmt(tx['final_weight'])} {unit}"],
        ]),
        Paragraph("4. Transaction", h2),
        table([
            ["Prix unitaire", _fmt(tx["unit_price"])],
            ["Montant total", _fmt(tx["total_amount"])],
            ["Référence séquestre", _fmt(tx["escrow_reference"])],
        ]),
        Paragraph("5. Impact environnemental", h2),
        table([
            ["Facteur CO₂ / unité", f"{_fmt(tx['co2_factor_per_unit'])} kg CO₂e"],
            ["CO₂ évité", f"{_fmt(tx['co2_saved_total'])} kg CO₂e"],
        ]),
        Paragraph("6. Traçabilité", h2),
        table([
            ["Réservation", _fmt(tx["created_at"])],
            ["Scan QR sur site", _fmt(tx["qr_scanned_at"])],
            ["Enlèvement / pesée", _fmt(tx["collected_at"])],
            ["Validation collecteur", _fmt(tx["collector_confirmed_at"])],
            ["Validation producteur", _fmt(tx["producer_confirmed_at"])],
        ]),
        Spacer(1, 6 * mm),
        Paragraph(f"Empreinte d'intégrité SHA-256 : {data['integrity_sha256']}", small),
        Paragraph("Document généré automatiquement par EcoLoop Circular Hub.", small),
    ]
    doc.build(story)
    return buf.getvalue()
