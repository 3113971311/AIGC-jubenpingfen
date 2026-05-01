import os
from typing import Optional


def parse_file(filepath: str, filename: str) -> tuple[str, str]:
    """
    解析文件，返回 (标题, 纯文本内容)
    支持 txt / docx / pdf
    """
    ext = os.path.splitext(filename)[1].lower()
    title = os.path.splitext(filename)[0]

    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    elif ext == ".docx":
        content, maybe_title = _parse_docx(filepath)
        if maybe_title:
            title = maybe_title
    elif ext == ".pdf":
        content = _parse_pdf(filepath)
    else:
        raise ValueError(f"不支持的文件格式: {ext}，请上传 txt/docx/pdf 文件")

    return title.strip() or "未命名剧本", content.strip()


def _parse_docx(filepath: str) -> tuple[str, Optional[str]]:
    from docx import Document

    doc = Document(filepath)
    paragraphs = []
    first_line = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            if first_line is None:
                first_line = text
            paragraphs.append(text)
    return "\n\n".join(paragraphs), first_line


def _parse_pdf(filepath: str) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(filepath)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)
