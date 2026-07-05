"""Pipeline step 1 — chunk documents by heading/slide boundary.

See docs/concept-graph-pipeline.md step 1. Deliberately does not chunk by a
hard character count: a fixed-size window can cut a concept in half, which
poisons concept extraction (step 2) downstream.
"""

from __future__ import annotations

import io
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    page: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def chunk_document(filename: str, content: bytes) -> list[Chunk]:
    """Dispatch to the right parser based on file extension and return
    boundary-aligned chunks for one document."""
    doc_id = filename
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix == ".pdf":
        return _chunk_pdf(doc_id, content)
    if suffix == ".pptx":
        return _chunk_pptx(doc_id, content)
    if suffix == ".docx":
        return _chunk_docx(doc_id, content)
    raise ValueError(f"Unsupported document type: {suffix or filename!r}")


def _chunk_pdf(doc_id: str, content: bytes) -> list[Chunk]:
    import fitz  # PyMuPDF

    chunks: list[Chunk] = []
    with fitz.open(stream=content, filetype="pdf") as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if not text:
                continue
            chunks.append(
                Chunk(doc_id=doc_id, chunk_id=f"{doc_id}:p{page_number}", page=page_number, text=text)
            )
    return chunks


def _chunk_pptx(doc_id: str, content: bytes) -> list[Chunk]:
    from pptx import Presentation

    chunks: list[Chunk] = []
    presentation = Presentation(io.BytesIO(content))
    for slide_number, slide in enumerate(presentation.slides, start=1):
        parts = [
            shape.text_frame.text.strip()
            for shape in slide.shapes
            if shape.has_text_frame and shape.text_frame.text.strip()
        ]
        text = "\n".join(parts)
        if not text:
            continue
        chunks.append(
            Chunk(doc_id=doc_id, chunk_id=f"{doc_id}:s{slide_number}", page=slide_number, text=text)
        )
    return chunks


def _chunk_docx(doc_id: str, content: bytes) -> list[Chunk]:
    # docx has no rendered page numbers; `page` here is the 1-indexed
    # heading-delimited section instead, which is the only stable locator
    # available without a rendering pass.
    from docx import Document

    document = Document(io.BytesIO(content))
    chunks: list[Chunk] = []
    section_number = 0
    buffer: list[str] = []

    def flush() -> None:
        nonlocal section_number
        text = "\n".join(buffer).strip()
        if text:
            section_number += 1
            chunks.append(
                Chunk(doc_id=doc_id, chunk_id=f"{doc_id}:h{section_number}", page=section_number, text=text)
            )
        buffer.clear()

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        is_heading = paragraph.style.name.lower().startswith(("heading", "title"))
        if is_heading and buffer:
            flush()
        buffer.append(text)
    flush()
    return chunks
