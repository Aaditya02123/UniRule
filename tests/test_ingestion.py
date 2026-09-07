import pytest
from pathlib import Path
import csv
import json
import fitz

from app.models.schemas import DocumentRecord
from app.services.ingestion import (
    ingest_markdown, 
    ingest_csv, 
    ingest_pdf, 
    ingest_corpus
)

# Test 1: Markdown Ingestion (Isolated)
def test_ingest_markdown(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Section A\nSome text.\n## Section B\nMore text.", encoding='utf-8')
    
    records = ingest_markdown(md_file)
    assert len(records) == 2
    assert records[0].section == "Section A"
    assert "Some text." in records[0].text
    assert "Section A" in records[0].text
    assert records[1].section == "Section B"
    assert "More text." in records[1].text
    assert records[0].file_type == "markdown"

# Test 2: CSV Ingestion (Isolated)
def test_ingest_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Requirement", "Deadline"])
        writer.writerow(["Fees", "Pay Tuition", "July 31"])
        
    records = ingest_csv(csv_file)
    assert len(records) == 1
    assert records[0].section == "Fees"
    assert "July 31" in records[0].text
    assert "Requirement: Pay Tuition" in records[0].text
    assert records[0].file_type == "csv"

# Test 3: PDF Ingestion (Isolated)
def test_ingest_pdf(tmp_path):
    from reportlab.pdfgen import canvas
    pdf_file = tmp_path / "test.pdf"
    
    c = canvas.Canvas(str(pdf_file))
    c.drawString(100, 750, "Medicaps University General Academic Regulations")
    c.drawString(100, 700, "Section 1: General Rule")
    c.drawString(100, 650, "Line of text 1.")
    c.showPage()
    c.drawString(100, 750, "Line of text 2.")
    c.drawString(100, 700, "Section 2: Another Rule")
    c.drawString(100, 650, "Line of text 3.")
    c.save()
    
    records = ingest_pdf(pdf_file)
    # Page 1 has title and Section 1 -> yields 2 records (Title block, then Section 1 block)
    # Page 2 has continuation of Section 1 and then Section 2 -> yields 2 records (Continuation block, then Section 2 block)
    assert records[0].page == 1
    assert "Medicaps University" in records[0].section
    
    assert records[1].page == 1
    assert "Section 1:" in records[1].section
    assert "Line of text 1" in records[1].text
    
    assert records[2].page == 2
    assert "Section 1:" in records[2].section
    assert "Line of text 2" in records[2].text
    
    assert records[3].page == 2
    assert "Section 2:" in records[3].section
    assert "Line of text 3" in records[3].text


# Test 4: Corpus Discovery (Isolated)
def test_ingest_corpus(tmp_path):
    (tmp_path / "test.md").write_text("# Test", encoding='utf-8')
    (tmp_path / "contradictions.json").write_text("{}", encoding='utf-8')
    (tmp_path / ".keep").write_text("", encoding='utf-8')
    
    records = list(ingest_corpus(tmp_path))
    assert len(records) == 1
    assert records[0].document == "test.md"


# Test 5: Critical Evidence Preservation Tests on Production Data
def test_evidence_preservation():
    data_dir = Path(Path(__file__).parent.parent, "data")
    if not data_dir.exists():
        pytest.skip("Data directory not found for production test.")
        
    records = list(ingest_corpus(data_dir))
    
    # 1. fee_schedule.csv ingestion preserves "July 31"
    fee_records = [r for r in records if r.document == "fee_schedule.csv"]
    assert any("July 31" in r.text for r in fee_records)
    
    # 2. hostel_handbook.pdf ingestion preserves "10:00 PM"
    hostel_records = [r for r in records if r.document == "hostel_handbook.pdf"]
    assert any("10:00 PM" in r.text for r in hostel_records)
    
    # 3. student_discipline.md ingestion preserves "11:00 PM"
    discipline_records = [r for r in records if r.document == "student_discipline.md"]
    assert any("11:00 PM" in r.text for r in discipline_records)
