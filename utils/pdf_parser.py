# utils/pdf_parser.py

def extract_text_from_pdf(uploaded_pdf):
    """Extract text from PDF file. Returns empty string if PDF parsing is not available."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except ImportError:
        print("Warning: PyMuPDF not available. PDF parsing will be disabled.")
        return ""
