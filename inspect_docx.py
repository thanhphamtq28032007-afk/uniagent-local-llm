from docx import Document
from docx.document import Document as DocumentObject
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


DOCX_PATH = r"E:\SAMPLE FINAL TEST-NEW.docx"
OUTPUT_TXT = "docx_lines.txt"


def iter_block_items(parent):
    """
    Đọc cả đoạn văn và bảng theo đúng thứ tự xuất hiện trong file Word.
    """
    if isinstance(parent, DocumentObject):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Không hỗ trợ kiểu parent này")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def main():
    doc = Document(DOCX_PATH)

    lines = []
    count = 1

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                lines.append(f"{count:04d} | P | {text}")
                count += 1

        elif isinstance(block, Table):
            for row in block.rows:
                cells = []
                for cell in row.cells:
                    cell_text = " ".join(
                        p.text.strip() for p in cell.paragraphs if p.text.strip()
                    )
                    cells.append(cell_text)

                row_text = " | ".join(cells).strip()
                if row_text:
                    lines.append(f"{count:04d} | T | {row_text}")
                    count += 1

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Đã xuất {len(lines)} dòng ra file {OUTPUT_TXT}")


if __name__ == "__main__":
    main()