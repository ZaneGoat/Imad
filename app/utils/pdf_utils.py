import os
import textwrap
from datetime import datetime
from tkinter import filedialog


from app.config import PDF_DIR


def _escape(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_objects(lines, title):
    page_width = 595
    page_height = 842
    margin = 45
    line_height = 15
    max_lines = 48
    pages = [lines[i : i + max_lines] for i in range(0, len(lines), max_lines)] or [[]]
    objects = []
    page_ids = []

    font_id = 3 + len(pages) * 2
    for page_index, page_lines in enumerate(pages, start=1):
        stream = ["BT", "/F1 11 Tf", f"{margin} {page_height - margin} Td"]
        for idx, line in enumerate(page_lines):
            prefix = "" if idx == 0 else f"0 -{line_height} Td "
            stream.append(f"{prefix}({_escape(line)}) Tj")
        stream.append("ET")
        content = "\n".join(stream)
        page_id = 3 + (page_index - 1) * 2
        content_id = page_id + 1
        page_ids.append(page_id)
        objects.append(
            f"{page_id} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>\n"
            "endobj\n"
        )
        objects.append(
            f"{content_id} 0 obj\n<< /Length {len(content.encode('latin-1', 'replace'))} >>\n"
            f"stream\n{content}\nendstream\nendobj\n"
        )

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    header_objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>\nendobj\n",
    ]
    font_object = f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n"
    return header_objects + objects + [font_object]


def create_pdf(filename, title, lines):
    os.makedirs(PDF_DIR, exist_ok=True)
    path = filedialog.asksaveasfilename(
        title="Enregistrer le PDF",
        defaultextension=".pdf",
        initialfile=filename,
        initialdir=os.path.abspath(PDF_DIR),
        filetypes=[("Fichiers PDF", "*.pdf")],
    )
    if not path:
        return None

    safe_lines = [title.upper(), "=" * min(len(title), 70), ""]
    for line in lines:
        wrapped = textwrap.wrap(str(line), width=88) or [""]
        safe_lines.extend(wrapped)
    safe_lines.extend(["", f"Genere le {datetime.now().strftime('%Y-%m-%d %H:%M')}"])

    objects = _pdf_objects(safe_lines, title)
    content = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(content.encode("latin-1", "replace")))
        content += obj
    xref_pos = len(content.encode("latin-1", "replace"))
    content += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n"
    content += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF"
    )

    with open(path, "wb") as f:
        f.write(content.encode("latin-1", "replace"))
    return os.path.abspath(path)


def open_pdf(path):
    if not path:
        return False
    try:
        os.startfile(path)
    except Exception:
        return False
    return True


def table_lines(headers, rows):
    headers = [str(h) for h in headers]
    rows = [[str(value) for value in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = min(max(widths[index], len(value)), 24)

    def fmt(row):
        return " | ".join(str(value)[: widths[i]].ljust(widths[i]) for i, value in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    result = [fmt(headers), separator]
    result.extend(fmt(row) for row in rows)
    return result
