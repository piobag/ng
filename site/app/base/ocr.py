from pdf2image import convert_from_bytes
import pytesseract


def extract_text_from_pdf(content):
    # Convert PDF to image
    pages = convert_from_bytes(content, 500)
     
    # Extract text from each page using Tesseract OCR
    text_data = ''
    for page in pages:
        text = pytesseract.image_to_string(page)
        text_data += text + '\n'
     
    # Return the text data
    return text_data
 
