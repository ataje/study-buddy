from pypdf import PdfReader

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 40
MAX_WORDS = 25000
MAX_SESSION_DOCUMENTS = 3


def extract_pdf(uploaded_file):
    uploaded_file.seek(0, 2)
    size = uploaded_file.tell()
    uploaded_file.seek(0)
    if size > MAX_BYTES:
        raise ValueError("Please choose a PDF smaller than 5 MB.")
    try:
        reader = PdfReader(uploaded_file)
        if reader.is_encrypted:
            raise ValueError("Please upload a PDF without password protection.")
        if len(reader.pages) > MAX_PAGES:
            raise ValueError("Please choose a lecture of 40 pages or fewer.")
        pages = []
        word_count = 0
        for number, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            word_count += len(text.split())
            if word_count > MAX_WORDS:
                raise ValueError("This lecture is too long. Please split it into smaller PDFs.")
            if text:
                pages.append({"page": number, "text": text})
    except ValueError:
        raise
    except Exception:
        raise ValueError("This PDF could not be read. Please try another file.") from None
    if not pages:
        raise ValueError("No readable text was found. Scanned PDFs need OCR before upload.")
    return "\n".join(page["text"] for page in pages), pages
