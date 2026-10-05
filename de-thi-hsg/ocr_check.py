import os
os.environ['TESSDATA_PREFIX'] = r'C:\Opencode\tessdata'
import pymupdf, pytesseract
from PIL import Image
import io

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

def ocr_one_page(path, page_idx):
    doc = pymupdf.open(path)
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes('png')))
    text = pytesseract.image_to_string(img, lang='fra')
    doc.close()
    return text

base = r'C:\Opencode\de-thi-hsg'

# Check all files page 1 to identify years
all_files = [
    '2021-2022.pdf',
    '2022-2023.pdf',
    'de-thi-2024-2025.pdf',
    'de-thi-2024-2025-moi.pdf',
    'de-thi-2025-2026.pdf',
]

for fname in all_files:
    path = os.path.join(base, fname)
    if os.path.exists(path):
        doc = pymupdf.open(path)
        pages = len(doc)
        text = ocr_one_page(path, 0)
        print(f'=== {fname} ({pages} pages) ===')
        print(text[:400])
        print()
        doc.close()

# Special: check "De thi HSGQG 2024-2025.pdf" using os.listdir
for f in os.listdir(base):
    if f.startswith('De') and f.endswith('.pdf'):
        path = os.path.join(base, f)
        doc = pymupdf.open(path)
        pages = len(doc)
        text = ocr_one_page(path, 0)
        print(f'=== {f} ({pages} pages) ===')
        print(text[:400])
        print()
        doc.close()
