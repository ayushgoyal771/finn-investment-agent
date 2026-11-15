"""Small, attributed historical evidence packs. These are paraphrases, not quotations.

Figures were checked against issuer annual reports and transcripts. No news or broker research.
Every pack remains visibly historical, regardless of the machine's current date.
"""
TCS_AR = "https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/ar/annual-report-2024-2025.pdf"
TCS_CALL = "https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2024-25/q4/Management%20Commentary/Transcript%20of%20the%20Q4%202024-25%20Earnings%20Conference%20Call%20held%20at%201900%20hrs%20IST%20on%20Apr%2010%2C%202025.pdf"
INFY_AR = "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-25.pdf"
INFY_CALL = "https://www.infosys.com/investors/reports-filings/quarterly-results/2024-2025/q4/documents/transcripts/earningscall.pdf"
ASIAN_AR = "https://www.asianpaints.com/content/dam/annual-folder-2425/pdf/Board_s%20Report.pdf"
ASIAN_CALL = "https://www.asianpaints.com/content/dam/asianpaints/website/secondary-navigation/investors/financial-results-2/2024-2025/Q4/Transcript-Q4_Investor_Meet_2025.pdf"


def fact(id, heading, text, url, title, kind, locator, tags):
    return {"id": id, "heading": heading, "text": text, "url": url, "title": title,
            "kind": kind, "locator": locator, "tags": tags, "paraphrase": True, "period": "FY2025"}


PACKS = {
    "TCS": {
        "name": "Tata Consultancy Services", "period": "FY2025 · year ended 31 March 2025",
        "thesis": "Deal conversion matters more than deal announcements.",
        "facts": [
            fact("tcs-growth", "Growth with a currency distinction", "FY2025 revenue was ₹255,324 crore: 6.0% reported growth and 4.2% in constant currency.", TCS_AR, "Integrated Annual Report 2024–25", "annual_report", "Letter from the CEO · printed page 11", ["revenue", "growth", "business"]),
            fact("tcs-margin", "Margins carry an investment cost", "FY2025 operating margin was 24.3%, versus 24.6% in FY2024 excluding the legal-claim settlement. Wage increases and capability investment were headwinds.", TCS_AR, "Integrated Annual Report 2024–25", "annual_report", "Financial Capital · printed page 21; MD&A", ["margin", "profit", "trajectory"]),
            fact("tcs-pat", "Profit attributable to shareholders", "FY2025 PAT attributable to shareholders was ₹48,553 crore. The annual report distinguishes operating profit from EBITDA; FINN does not substitute one for the other.", TCS_AR, "Integrated Annual Report 2024–25", "annual_report", "MD&A · consolidated financial results", ["pat", "profit", "financial"]),
            fact("tcs-call", "An order book is not a revenue forecast", "In the April 2025 call, management discussed macro uncertainty and delays in discretionary spending. This is qualitative commentary, not a numeric growth guarantee.", TCS_CALL, "Q4 FY2025 earnings call · 10 April 2025", "transcript", "Opening management commentary and Q&A", ["guidance", "narrative", "deals", "risk"]),
        ],
        "metrics": [{"label": "Revenue", "value": 255324, "unit": "₹ crore", "source_id": "tcs-growth"},
                    {"label": "Operating margin", "value": 24.3, "unit": "%", "source_id": "tcs-margin"},
                    {"label": "PAT · owners", "value": 48553, "unit": "₹ crore", "source_id": "tcs-pat"}],
        "questions": ["Which public indicators show large deals entering billable delivery?", "Can utilisation gains offset continued investment without hurting execution?"],
    },
    "INFY": {
        "name": "Infosys", "period": "FY2025 · year ended 31 March 2025",
        "thesis": "Strong cash conversion deserves a closer look at what drove it.",
        "facts": [
            fact("infy-revenue", "Reported growth and constant currency differ", "FY2025 consolidated revenue was ₹162,990 crore versus ₹153,670 crore in FY2024: 6.1% reported growth and 4.2% in constant currency.", INFY_AR, "Integrated Annual Report 2024–25", "annual_report", "Business highlights · printed pages 28–29", ["growth", "revenue", "trajectory", "business"]),
            fact("infy-margin", "Profitability held above 21%", "FY2025 operating margin was 21.1%. Net profit attributable to owners was ₹26,713 crore under the report’s IFRS consolidated presentation.", INFY_AR, "Integrated Annual Report 2024–25", "annual_report", "Business highlights · printed pages 28–29", ["margin", "pat", "profit", "financial"]),
            fact("infy-cash", "Cash conversion outpaced accounting profit", "FY2025 free cash flow was ₹34,549 crore, with reported FCF conversion of 129.2% of net profit. Cash and investments were ₹47,549 crore under the report’s definition.", INFY_AR, "Integrated Annual Report 2024–25", "annual_report", "Business highlights · printed pages 28–29 and footnotes", ["cash", "balance", "debt", "quality"]),
            fact("infy-guidance", "A dated forward expectation, not a delivered result", "On 17 April 2025, management guided FY2026 constant-currency revenue growth of 0–3% and operating margin of 20–22%. These are historical forward expectations; this pack does not establish whether they were delivered.", INFY_CALL, "Q4 FY2025 earnings call · 17 April 2025", "transcript", "PDF pages 4 and 8 · CEO/CFO commentary", ["guidance", "narrative", "growth", "margin"]),
        ],
        "metrics": [{"label": "Revenue", "value": 162990, "unit": "₹ crore", "source_id": "infy-revenue"},
                    {"label": "Operating margin", "value": 21.1, "unit": "%", "source_id": "infy-margin"},
                    {"label": "Free cash flow", "value": 34549, "unit": "₹ crore", "source_id": "infy-cash"}],
        "questions": ["Which working-capital movements supported cash conversion, and are they repeatable?", "How does cash generation compare with profit after adjusting for tax timing?"],
    },
    "ASIANPAINT": {
        "name": "Asian Paints", "period": "FY2025 · year ended 31 March 2025",
        "thesis": "Volume alone does not tell the demand story.",
        "facts": [
            fact("asian-revenue", "Revenue declined on a consolidated basis", "FY2025 consolidated revenue from sales and other operating income was ₹33,905.62 crore, versus ₹35,494.73 crore in FY2024, a 4.5% decline.", ASIAN_AR, "Annual Report 2024–25 · Board’s Report", "annual_report", "Financial Results and State of Company Affairs · opening table", ["revenue", "growth", "financial"]),
            fact("asian-ebitda", "Earnings fell faster than revenue", "Consolidated EBITDA declined from ₹8,272.94 crore to ₹6,578.82 crore, down 20.5%. Use the report’s EBITDA definition when comparing periods.", ASIAN_AR, "Annual Report 2024–25 · Board’s Report", "annual_report", "Financial Results and State of Company Affairs · opening table", ["margin", "ebitda", "profit", "trajectory"]),
            fact("asian-volume", "Decorative volume and value diverged", "For Q4 FY2025, management reported India decorative volume growth of 1.8% and value decline of 5.2%. These segment figures are distinct from consolidated annual revenue.", ASIAN_CALL, "Q4 FY2025 investor conference · 8 May 2025", "transcript", "Printed page 3 · Decorative Business (India)", ["volume", "pricing", "narrative", "demand", "business"]),
            fact("asian-demand", "Management described a difficult market", "Management described suppressed demand and increased competition. Full-year India decorative volumes grew 2.5% while value declined 5.7%.", ASIAN_CALL, "Q4 FY2025 investor conference · 8 May 2025", "transcript", "Printed page 3 · management commentary", ["risk", "guidance", "narrative", "competition"]),
        ],
        "metrics": [{"label": "Revenue", "value": 33905.62, "unit": "₹ crore", "source_id": "asian-revenue"},
                    {"label": "EBITDA", "value": 6578.82, "unit": "₹ crore", "source_id": "asian-ebitda"},
                    {"label": "Q4 decorative volume", "value": 1.8, "unit": "% YoY", "source_id": "asian-volume"}],
        "questions": ["How much of the value decline reflects price reductions versus downtrading?", "What public channel data would confirm a recovery in demand quality?"],
    },
}

# Issuer-hosted fallbacks are limited to these verified URLs. Generic research discovers exchange originals.
ISSUER_DOCUMENTS = {
    "TCS": [{"url": TCS_AR, "title": "TCS Annual Report FY2025", "kind": "annual_report"}, {"url": TCS_CALL, "title": "TCS Q4 FY2025 call", "kind": "transcript"}],
    "INFY": [{"url": INFY_AR, "title": "Infosys Annual Report FY2025", "kind": "annual_report"}, {"url": INFY_CALL, "title": "Infosys Q4 FY2025 call", "kind": "transcript"}],
    "ASIANPAINT": [{"url": ASIAN_AR, "title": "Asian Paints FY2025 Board’s Report", "kind": "annual_report"}, {"url": ASIAN_CALL, "title": "Asian Paints Q4 FY2025 call", "kind": "transcript"}],
}
