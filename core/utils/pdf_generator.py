from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.fonts import addMapping
from datetime import datetime
import os

pdfmetrics.registerFont(TTFont("DejaVuSans", "assets/fonts/DejaVuSans.ttf"))
addMapping("DejaVuSans", 0, 0, "DejaVuSans")


def generate_pdf_report(
    repo_url: str ,
    summary_text: str ,
    structure_text: str = None,
    dependencies_text: str = None
):
    """
    Membuat laporan PDF hasil analisis repository GitHub.
    """
    # Nama file output
    filename = f"GitCortex_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # Setup dokumen
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Gaya khusus
    body_style = ParagraphStyle(
    name="Body",
    fontName="DejaVuSans",
    fontSize=11,
    leading=14,
)

    title_style = ParagraphStyle(
        name="Title",
        fontName="DejaVuSans",
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        leading=22,
    )

    header_style = styles["Heading2"]

    # Tambahkan konten
    story.append(Paragraph("Git-Cortex Repository Analysis Report", title_style))
    story.append(Paragraph(f"Repository URL: {repo_url}", body_style))
    story.append(Spacer(1, 0.3 * inch))

    # Ringkasan umum
    story.append(Paragraph("1. Repository Summary", header_style))
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Struktur repo
    if structure_text:
        story.append(Paragraph("2. Repository Structure", header_style))
        story.append(Paragraph(f"<pre>{structure_text}</pre>", body_style))
        story.append(Spacer(1, 0.2 * inch))

    # Dependency analysis
    if dependencies_text:
        story.append(Paragraph("3. Dependencies Analysis", header_style))
        story.append(Paragraph(dependencies_text, body_style))

    # Buat PDF
    doc.build(story)

    return filepath
