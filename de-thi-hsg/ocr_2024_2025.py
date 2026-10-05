import os
os.environ['TESSDATA_PREFIX'] = r'C:\Opencode\tessdata'
import pymupdf, pytesseract
from PIL import Image
import io

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

def ocr_pdf_full(pdf_path, label):
    doc = pymupdf.open(pdf_path)
    total = len(doc)
    print("\n" + "#"*80)
    print(f"# {label} ({total} trang)")
    print("#"*80)
    
    for i in range(total):
        page = doc[i]
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes('png')))
        text = pytesseract.image_to_string(img, lang='fra')
        print(f"\n--- TRANG {i+1}/{total} ---")
        print(text)
    
    doc.close()

base = r'C:\Opencode\de-thi-hsg'

# De thi 2024-2025 (16 trang - day du nhat)
ocr_pdf_full(os.path.join(base, 'de-thi-2024-2025-moi.pdf'), 'DE THI HSGQG TIENG PHAP 2024-2025')
