# utils.py
import fitz  # PyMuPDF
from PIL import Image
import io
import pytesseract
from typing import List, Tuple

def extract_text_and_images_from_pdf(path: str):
    """
    Extracts text (concatenated) and embedded images from a PDF.
    Returns (text, list_of_pil_images)
    """
    doc = fitz.open(path)
    text_parts = []
    images = []
    for page in doc:
        text_parts.append(page.get_text("text"))

        # Extract images
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            images.append(pil_image)

    return "\n".join(text_parts), images

def ocr_image(pil_image: Image.Image) -> str:
    """
    Runs Tesseract OCR on a PIL image and returns extracted text.
    """
    text = pytesseract.image_to_string(pil_image)
    return text

def extract_text_from_image_file(path: str) -> str:
    img = Image.open(path).convert("RGB")
    return ocr_image(img)
