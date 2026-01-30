import fitz  # PyMuPDF

def extract_text_from_pdf(file_field):
    """
    Extract text from PDF using PyMuPDF.
    """
    file_field.seek(0)
    pdf_bytes = file_field.read()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""

    for page in doc:
        text += page.get_text("text") + " "

    return text.strip()
