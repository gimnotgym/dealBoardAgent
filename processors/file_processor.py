"""
파일 처리 모듈 - PDF / DOCX / TXT / JPG 에서 텍스트 추출
"""
import io
from pathlib import Path


def extract_text_from_file(uploaded_file) -> str:
    """Streamlit UploadedFile 객체에서 텍스트를 추출합니다."""
    filename = uploaded_file.name.lower()
    content = uploaded_file.read()

    if filename.endswith(".txt"):
        return _extract_txt(content)
    elif filename.endswith(".pdf"):
        return _extract_pdf(content)
    elif filename.endswith(".docx"):
        return _extract_docx(content)
    elif filename.endswith((".jpg", ".jpeg", ".png")):
        return _extract_image(content)
    else:
        return f"[지원하지 않는 파일 형식: {filename}]"


def _extract_txt(content: bytes) -> str:
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _extract_pdf(content: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages) if pages else "[PDF에서 텍스트를 추출할 수 없습니다]"
    except ImportError:
        return "[pdfplumber 미설치: pip install pdfplumber]"
    except Exception as e:
        return f"[PDF 처리 오류: {e}]"


def _extract_docx(content: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs) if paragraphs else "[DOCX에서 텍스트를 추출할 수 없습니다]"
    except ImportError:
        return "[python-docx 미설치: pip install python-docx]"
    except Exception as e:
        return f"[DOCX 처리 오류: {e}]"


def _extract_image(content: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img, lang="kor+eng")
        return text.strip() if text.strip() else "[이미지에서 텍스트를 인식할 수 없습니다]"
    except ImportError:
        return "[pytesseract/Pillow 미설치 또는 Tesseract 미설치]"
    except Exception as e:
        return f"[이미지 처리 오류: {e}]"
