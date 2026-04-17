"""
Invoice PDF generator — produces invoices matching the example format:

  MEIJER Aurélie                          [Client Name]
  126 Route de Marny                      [Client Address]
  74330 Poisy
  France
  SIREN : 879 762 151
                                          Date : DD-MM-YYYY

  FACTURE YYYY-NNN
  ─────────────────────────────────────────

  | Prestations         | HEURES | TARIF HORAIRE | TOTAL |
  | Cours du DD-MM-YYYY | 1.50   | 40.00         | 60.00 |
  ...
                          TOTAL HT / PRIX GLOBAL EN EUROS  XXX.XX
                          TVA non applicable, art. 293 B du CGI

  Mode de règlement : virement bancaire
  Paiement dû dans les 30 jours à partir de la date de la facture
  Nom :   Mme MEIJER Aurelie
  IBAN :  FR76 4061 8804 9800 0408 0951 873
  BIC :   BOUS FRPP XXX
"""

import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

from services.tracker_service import get_client_folder

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# ── Your company details (edit these) ────────────────────────────────
COMPANY = {
    "name": "MEIJER Aurélie",
    "address_line1": "126 Route de Marny",
    "address_line2": "74330 Poisy",
    "address_line3": "France",
    "siren": "879 762 151",
    "bank_name": "Mme MEIJER Aurelie",
    "iban": "FR76 4061 8804 9800 0408 0951 873",
    "bic": "BOUS FRPP XXX",
}
# ─────────────────────────────────────────────────────────────────────


def _get_next_invoice_number(client_name, year):
    """
    Determine the next invoice number based on existing files in the client's folder.
    Format: YYYY-NNN (e.g. 2026-001, 2026-002).
    """
    client_folder = get_client_folder(client_name, year)
    os.makedirs(client_folder, exist_ok=True)
    existing = []

    for f in os.listdir(client_folder):
        if f.startswith(f"Facture {year}-") and f.endswith(".pdf"):
            try:
                # Extract number from "Facture 2026-005- Client.pdf"
                parts = f.replace(f"Facture {year}-", "").split("-")
                num = int(parts[0].strip())
                existing.append(num)
            except (ValueError, IndexError):
                pass

    next_num = max(existing, default=0) + 1
    return f"{year}-{next_num:03d}"


def generate_invoice(client, appointments, invoice_number=None, is_correction=False):
    """
    Generate a PDF invoice.

    Args:
        client:       dict — client data from client_service
        appointments: list of dicts with keys: date, duration_hours, duration_display, amount
        invoice_number: str — optional override, otherwise auto-generated
        is_correction: bool — whether this is a correction

    Returns:
        tuple — (filepath, final_invoice_number, total_amount)
    """
    year = datetime.datetime.now().year
    client_name = client.get("name", "Client")
    client_folder = get_client_folder(client_name, year)
    os.makedirs(client_folder, exist_ok=True)

    if not invoice_number:
        invoice_number = _get_next_invoice_number(client_name, year)

    filename = f"Facture {invoice_number}- {client_name}.pdf"
    filepath = os.path.join(client_folder, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Custom styles ────────────────────────────────────────────────
    style_normal = ParagraphStyle(
        "InvNormal", parent=styles["Normal"], fontName="Helvetica", fontSize=10,
        leading=14,
    )
    style_bold = ParagraphStyle(
        "InvBold", parent=style_normal, fontName="Helvetica-Bold",
    )
    style_right = ParagraphStyle(
        "InvRight", parent=style_normal, alignment=TA_RIGHT,
    )
    style_title = ParagraphStyle(
        "InvTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=14, leading=18, spaceAfter=2 * mm,
    )
    style_small = ParagraphStyle(
        "InvSmall", parent=style_normal, fontSize=9, leading=12,
    )
    style_small_right = ParagraphStyle(
        "InvSmallRight", parent=style_small, alignment=TA_RIGHT,
    )
    style_small_italic = ParagraphStyle(
        "InvSmallItalic", parent=style_small, fontName="Helvetica-Oblique",
    )
    style_small_italic_right = ParagraphStyle(
        "InvSmallItalicRight", parent=style_small_italic, alignment=TA_RIGHT,
    )

    # ── Header: sender + recipient side by side ──────────────────────
    sender_lines = [
        COMPANY["name"],
        COMPANY["address_line1"],
        COMPANY["address_line2"],
        COMPANY["address_line3"],
        "",
        f"SIREN : {COMPANY['siren']}",
    ]

    # Build recipient lines
    recipient_lines = []
    title = client.get("title", "")
    if title:
        recipient_lines.append(f"{title} {client_name}")
    else:
        recipient_lines.append(client_name)

    if client.get("address_line1"):
        recipient_lines.append(str(client["address_line1"]))
    if client.get("address_line2"):
        recipient_lines.append(str(client["address_line2"]))
    if client.get("address_line3"):
        recipient_lines.append(str(client["address_line3"]))
    if client.get("phone"):
        recipient_lines.append(str(client["phone"]))

    sender_text = "<br/>".join(sender_lines)
    recipient_text = "<br/>".join(recipient_lines)

    header_table = Table(
        [[Paragraph(sender_text, style_normal), Paragraph(recipient_text, style_right)]],
        colWidths=[90 * mm, 70 * mm], hAlign='LEFT'
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)



    # ── Date ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 12 * mm))
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    story.append(Paragraph(f"Date : {today}", style_right))

    # ── Invoice title ────────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"<b>FACTURE {invoice_number}</b>", style_title))

    # Horizontal rule
    rule_table = Table([[""]], colWidths=[160 * mm], hAlign='LEFT')
    rule_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 2, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(rule_table)

    # ── Line items table ─────────────────────────────────────────────
    story.append(Spacer(1, 8 * mm))

    table_data = [
        [
            Paragraph("<b>Prestations</b>", style_normal),
            Paragraph("<b>HEURES</b>", style_normal),
            Paragraph("<b>TARIF HORAIRE</b>", style_right),
            Paragraph("<b>TOTAL</b>", style_right),
        ]
    ]

    total_amount = 0
    for apt in appointments:
        date_str = apt.get("date", "")
        desc = apt.get("description", "")
        if not desc and date_str:
            desc = f"Cours du {date_str}"
            
        duration_display = apt.get("duration_display", "")
        hourly_rate = float(apt.get("hourly_rate", client.get("hourly_rate", 0)))
        amount = float(apt.get("amount", 0))
        total_amount += amount

        table_data.append([
            Paragraph(desc, style_normal),
            Paragraph(str(duration_display), style_normal),
            Paragraph(f"{hourly_rate:.2f}", style_right),
            Paragraph(f"{amount:.2f}", style_right),
        ])

    col_widths = [80 * mm, 22 * mm, 30 * mm, 28 * mm]
    items_table = Table(table_data, colWidths=col_widths, hAlign='LEFT')
    items_table.setStyle(TableStyle([
        # Header row
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)

    # ── Total row ────────────────────────────────────────────────────
    # Determine label based on client type
    has_vat = bool(client.get("vat_number"))
    total_label = "TOTAL HT" if has_vat else "PRIX GLOBAL EN EUROS"

    total_table_data = [
        [
            "",
            Paragraph(f"<b>{total_label}</b>", style_normal),
            Paragraph(f"<b>{total_amount:.2f}</b>", style_right),
        ]
    ]
    total_table = Table(total_table_data, colWidths=[80 * mm, 52 * mm, 28 * mm], hAlign='LEFT')
    total_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOX", (2, 0), (2, 0), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(total_table)

    # ── Tax note ─────────────────────────────────────────────────────
    story.append(Spacer(1, 2 * mm))
    if has_vat:
        story.append(Paragraph(f"N° TVA : {client['vat_number']}", style_small_right))
    else:
        story.append(Paragraph("TVA non applicable, art. 293 B du CGI", style_small_italic_right))

    # ── Payment information ──────────────────────────────────────────
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "<b>Mode de règlement :</b> virement bancaire", style_normal
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "<i>Paiement dû dans les 30 jours à partir de<br/>"
        "la date de la facture</i>",
        style_small_italic,
    ))
    story.append(Spacer(1, 4 * mm))

    bank_data = [
        ["Nom :", COMPANY["bank_name"]],
        ["IBAN :", COMPANY["iban"]],
        ["BIC :", COMPANY["bic"]],
    ]
    bank_table = Table(bank_data, colWidths=[15 * mm, 80 * mm], hAlign='LEFT')
    bank_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(bank_table)

    # ── Build PDF ────────────────────────────────────────────────────
    doc.build(story)
    return filepath, invoice_number, total_amount
