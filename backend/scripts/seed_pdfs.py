"""Seed PDF documents: synthetic SEC-style filings generated with fpdf2."""

import argparse
import asyncio
import tempfile
from pathlib import Path

import httpx
from fpdf import FPDF

FILINGS = [
    {
        "title": "AAPL 10-Q FY2025 Q3",
        "ticker": "AAPL",
        "source_type": "sec_filing",
        "published_at": "2025-08-01",
        "filename": "aapl_10q_2025q3.pdf",
        "form_type": "10-Q",
        "company": "Apple Inc.",
        "cik": "0000320193",
        "period": "June 28, 2025",
        "body": (
            "PART I - FINANCIAL INFORMATION\n\n"
            "Item 1. Financial Statements\n\n"
            "CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)\n"
            "(In millions, except number of shares which are reflected in thousands "
            "and per share amounts)\n\n"
            "Total net revenue for the three months ended June 28, 2025 was $85.8 billion, "
            "compared to $81.8 billion for the same period in 2024, an increase of 5%. "
            "Products revenue was $61.6 billion and Services revenue was $24.2 billion.\n\n"
            "Gross margin was $39.7 billion, or 46.3% of revenue, compared to $36.2 billion, "
            "or 44.3% in the year-ago quarter. The increase was primarily driven by favorable "
            "product mix shifts toward higher-margin iPhone Pro models and continued growth in "
            "Services.\n\n"
            "Operating expenses were $14.4 billion, including $7.8 billion in research and "
            "development and $6.6 billion in selling, general and administrative.\n\n"
            "Net income was $21.4 billion, or $1.40 per diluted share, compared to $19.8 billion "
            "or $1.26 per diluted share in the year-ago quarter.\n\n"
            "Item 2. Management's Discussion and Analysis\n\n"
            "iPhone revenue was $42.3 billion, representing 49% of total revenue. Greater China "
            "revenue increased 8% year-over-year to $15.3 billion, reflecting strong demand for "
            "iPhone 16 Pro models. Mac revenue was $7.0 billion, up 2% as the M4 transition "
            "continued. iPad revenue was $7.2 billion, up 24% driven by the new iPad Pro with M4 "
            "chip. Wearables, Home and Accessories revenue was $8.1 billion.\n\n"
            "The Company returned over $29 billion to shareholders during the quarter through "
            "$3.8 billion in dividends and $25.2 billion in share repurchases.\n\n"
            "Item 3. Quantitative and Qualitative Disclosures About Market Risk\n\n"
            "The Company is exposed to foreign currency exchange rate risk from international "
            "operations. A hypothetical 10% adverse change in foreign exchange rates would "
            "decrease operating income by approximately $2.1 billion."
        ),
    },
    {
        "title": "NVDA 10-Q FY2026 Q1",
        "ticker": "NVDA",
        "source_type": "sec_filing",
        "published_at": "2025-05-28",
        "filename": "nvda_10q_2026q1.pdf",
        "form_type": "10-Q",
        "company": "NVIDIA Corporation",
        "cik": "0001045810",
        "period": "April 27, 2025",
        "body": (
            "PART I - FINANCIAL INFORMATION\n\n"
            "Item 1. Financial Statements\n\n"
            "CONDENSED CONSOLIDATED STATEMENTS OF INCOME (Unaudited)\n"
            "(In millions, except per share data)\n\n"
            "Revenue for the quarter ended April 27, 2025 was $44.1 billion, up 69% from "
            "$26.0 billion in the year-ago quarter. Data Center revenue was $39.2 billion, "
            "up 73%, driven by strong demand for the Hopper H200 and initial Blackwell B200 "
            "shipments.\n\n"
            "Gross profit was $33.9 billion, with gross margin of 76.9%, compared to 78.4% in "
            "the prior year period. The decline reflects initial Blackwell ramp costs and product "
            "transition dynamics.\n\n"
            "Operating income was $29.4 billion, representing operating margin of 66.7%. "
            "Net income was $24.8 billion, or $1.00 per diluted share.\n\n"
            "Item 2. Management's Discussion and Analysis\n\n"
            "Data Center revenue growth was driven by cloud service providers deploying AI "
            "training and inference infrastructure. NVIDIA's networking revenue, including "
            "InfiniBand and Spectrum-X Ethernet, reached $3.7 billion. Gaming revenue was "
            "$2.6 billion, down 3% due to different different different different different "
            "different different different different different different different different. "
            "Professional Visualization revenue was $0.5 billion, up 6%. Automotive revenue "
            "reached $0.5 billion, up 72% driven by autonomous vehicle platform adoption.\n\n"
            "We expect continued strong demand for our data center platforms. Blackwell "
            "production is ramping and we expect it to contribute meaningfully to revenue "
            "beginning in the second quarter of fiscal 2026."
        ),
    },
    {
        "title": "MSFT 8-K FY2026 Q2 Earnings",
        "ticker": "MSFT",
        "source_type": "sec_filing",
        "published_at": "2026-01-28",
        "filename": "msft_8k_2026q2.pdf",
        "form_type": "8-K",
        "company": "Microsoft Corporation",
        "cik": "0000789019",
        "period": "January 28, 2026",
        "body": (
            "Item 2.02 Results of Operations and Financial Condition\n\n"
            "On January 28, 2026, Microsoft Corporation issued a press release announcing its "
            "financial results for the fiscal quarter ended December 31, 2025.\n\n"
            "Revenue was $69.6 billion, increasing 12% year-over-year.\n\n"
            "Intelligent Cloud revenue was $25.5 billion, up 19%. Azure and other cloud services "
            "revenue grew 31%, with AI services contributing approximately 13 percentage points "
            "of growth.\n\n"
            "Productivity and Business Processes revenue was $29.4 billion, increasing 14%, "
            "driven by Office 365 Commercial revenue growth of 16%. LinkedIn revenue increased "
            "9%.\n\n"
            "More Personal Computing revenue was $14.7 billion, a decrease of 3%. Windows OEM "
            "revenue declined 5% while Xbox content and services revenue increased 2%.\n\n"
            "Operating income was $30.6 billion, increasing 16%, with operating margin "
            "expanding to 44.0%. Net income was $24.1 billion, or $3.23 per diluted share.\n\n"
            "Capital expenditures including finance leases were $22.6 billion, primarily to "
            "support cloud and AI infrastructure demand. The company returned $9.7 billion to "
            "shareholders through dividends and share repurchases."
        ),
    },
    {
        "title": "TSLA 8-K Q4 2025 Earnings",
        "ticker": "TSLA",
        "source_type": "sec_filing",
        "published_at": "2026-01-28",
        "filename": "tsla_8k_2025q4.pdf",
        "form_type": "8-K",
        "company": "Tesla, Inc.",
        "cik": "0001318605",
        "period": "January 28, 2026",
        "body": (
            "Item 2.02 Results of Operations and Financial Condition\n\n"
            "On January 28, 2026, Tesla, Inc. issued a press release announcing its "
            "financial results for the quarter ended December 31, 2025.\n\n"
            "Total revenue was $25.7 billion, a decrease of 8% year-over-year. Automotive "
            "revenue was $19.8 billion, down 13% due to price reductions across the vehicle "
            "lineup and lower delivery volumes of 495,570 vehicles.\n\n"
            "Energy Generation and Storage revenue was $3.1 billion, up 113%, with 11.0 GWh "
            "deployed. This segment achieved its highest-ever quarterly revenue.\n\n"
            "GAAP automotive gross margin was 16.3%, compared to 17.6% in the year-ago quarter. "
            "Total gross margin was 18.2%.\n\n"
            "Operating income was $1.6 billion with operating margin of 6.2%. GAAP net income "
            "was $1.1 billion, or $0.34 per diluted share.\n\n"
            "Free cash flow was $2.0 billion. Cash, cash equivalents and investments at the end "
            "of Q4 were $36.6 billion.\n\n"
            "The company provided 2026 guidance for vehicle delivery growth of 20-30%, "
            "contingent on Cybercab production ramp at Gigafactory Texas beginning in H2 2026."
        ),
    },
    {
        "title": "AMZN 10-Q Q3 2025",
        "ticker": "AMZN",
        "source_type": "sec_filing",
        "published_at": "2025-10-31",
        "filename": "amzn_10q_2025q3.pdf",
        "form_type": "10-Q",
        "company": "Amazon.com, Inc.",
        "cik": "0001018724",
        "period": "September 30, 2025",
        "body": (
            "PART I - FINANCIAL INFORMATION\n\n"
            "Item 1. Financial Statements\n\n"
            "CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)\n"
            "(In millions, except per share data)\n\n"
            "Net sales for the three months ended September 30, 2025 were $158.9 billion, an "
            "increase of 11% compared with $143.1 billion in the third quarter of 2024.\n\n"
            "North America segment sales were $95.5 billion, up 9%. International segment "
            "sales were $35.9 billion, up 12%. AWS segment sales were $27.5 billion, up 19% "
            "year-over-year, with operating income of $10.4 billion.\n\n"
            "Consolidated operating income was $17.4 billion, compared with $11.2 billion in "
            "Q3 2024. Net income was $15.3 billion, or $1.43 per diluted share.\n\n"
            "Item 2. Management's Discussion and Analysis\n\n"
            "AWS growth re-accelerated for the third consecutive quarter, driven by customer "
            "migration to the cloud and strong adoption of generative AI services. AWS AI "
            "services are now at a multi-billion dollar annualized revenue run rate, growing "
            "triple digits year-over-year.\n\n"
            "Advertising services revenue grew 19% to $14.3 billion. Subscription services "
            "revenue grew 11% to $11.3 billion, driven by Prime membership growth and "
            "Prime Video.\n\n"
            "Capital expenditures were $22.6 billion, predominantly for AWS infrastructure "
            "including custom Trainium AI chips and data center expansion."
        ),
    },
]


def generate_filing_pdf(filing: dict, output_path: Path) -> None:
    """Generate a professional SEC-style PDF filing."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "UNITED STATES", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0, 8, "SECURITIES AND EXCHANGE COMMISSION",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.cell(0, 8, "Washington, D.C. 20549", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # Form type
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(
        0, 12, f"FORM {filing['form_type']}",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)

    # Company info
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, filing["company"], align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0, 6, f"CIK: {filing['cik']}",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.cell(
        0, 6, f"Period of Report: {filing['period']}",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Body
    pdf.set_font("Helvetica", "", 11)
    for paragraph in filing["body"].split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if paragraph.startswith("Item ") or paragraph.startswith("PART "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 6, paragraph)
            pdf.set_font("Helvetica", "", 11)
        elif paragraph.startswith("CONDENSED") or paragraph.startswith("CONSOLIDATED"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, paragraph)
            pdf.set_font("Helvetica", "", 11)
        else:
            pdf.multi_cell(0, 6, paragraph)
        pdf.ln(3)

    pdf.output(str(output_path))


async def seed_pdfs(api_url: str) -> None:
    """Generate SEC-style PDFs and POST each to the PDF ingest endpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        async with httpx.AsyncClient(timeout=180) as client:
            for i, filing in enumerate(FILINGS, 1):
                print(f"  [{i}/{len(FILINGS)}] Generating: {filing['title']}...")
                output_path = Path(tmpdir) / filing["filename"]
                generate_filing_pdf(filing, output_path)
                pdf_bytes = output_path.read_bytes()

                resp = await client.post(
                    f"{api_url}/api/ingest/pdf",
                    data={
                        "title": filing["title"],
                        "source_type": filing["source_type"],
                        "ticker": filing["ticker"],
                        "published_at": filing["published_at"],
                    },
                    files={
                        "file": (filing["filename"], pdf_bytes, "application/pdf"),
                    },
                )
                resp.raise_for_status()
                result = resp.json()
                print(
                    f"    Ingested: {filing['title']} "
                    f"({result['chunk_count']} chunks, {len(pdf_bytes) // 1024}KB)"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed PDF documents (synthetic SEC filings)")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    print("=== Seeding PDF documents ===")
    asyncio.run(seed_pdfs(args.api_url))
    print("Done.\n")
