import os
import re
import pandas as pd
from docx import Document
from docx.document import Document as DocumentObject
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


DOCX_PATH = r"E:\SAMPLE FINAL TEST-NEW.docx"
OUTPUT_CSV = r"data\public_test.csv"


def clean_text(text: str) -> str:
    text = text.replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def iter_block_items(parent):
    if isinstance(parent, DocumentObject):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Unsupported parent type")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def read_docx_text(docx_path: str) -> str:
    doc = Document(docx_path)
    parts = []

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = clean_text(block.text)
            if text:
                parts.append(text)

        elif isinstance(block, Table):
            for row in block.rows:
                row_parts = []
                for cell in row.cells:
                    cell_text = " ".join(
                        clean_text(p.text)
                        for p in cell.paragraphs
                        if clean_text(p.text)
                    )
                    if cell_text:
                        row_parts.append(cell_text)

                if row_parts:
                    parts.append(" ".join(row_parts))

    return clean_text(" ".join(parts))


def find_question_starts(text: str):
    """
    Tìm vị trí các câu hỏi dạng:
    1. ...
    2. ...
    15. ...
    """
    return list(re.finditer(r"(?<!\w)(\d{1,3})\.\s*", text))


def parse_question(qid: int, chunk: str):
    """
    Tách một câu hỏi thành:
    question, A, B, C, D
    """

    # Bỏ số thứ tự ở đầu
    chunk = re.sub(rf"^{qid}\.\s*", "", chunk).strip()

    # Tìm A. B. C. D.
    option_pattern = r"\b([A-D])\.\s*"
    option_matches = list(re.finditer(option_pattern, chunk))

    if len(option_matches) < 4:
        return {
            "qid": qid,
            "question": clean_text(chunk),
            "A": "",
            "B": "",
            "C": "",
            "D": ""
        }

    # Lấy lần xuất hiện đầu tiên của A/B/C/D
    pos = {}
    for m in option_matches:
        letter = m.group(1)
        if letter not in pos:
            pos[letter] = m

    if not all(x in pos for x in ["A", "B", "C", "D"]):
        return {
            "qid": qid,
            "question": clean_text(chunk),
            "A": "",
            "B": "",
            "C": "",
            "D": ""
        }

    a = pos["A"]
    b = pos["B"]
    c = pos["C"]
    d = pos["D"]

    question = chunk[:a.start()]
    option_a = chunk[a.end():b.start()]
    option_b = chunk[b.end():c.start()]
    option_c = chunk[c.end():d.start()]
    option_d = chunk[d.end():]

    return {
        "qid": qid,
        "question": clean_text(question),
        "A": clean_text(option_a),
        "B": clean_text(option_b),
        "C": clean_text(option_c),
        "D": clean_text(option_d)
    }


def convert_docx_to_csv():
    if not os.path.exists(DOCX_PATH):
        print("Không tìm thấy file Word:", DOCX_PATH)
        return

    os.makedirs("data", exist_ok=True)

    text = read_docx_text(DOCX_PATH)

    print("Đã đọc Word.")
    print("Độ dài văn bản:", len(text))

    starts = find_question_starts(text)

    print("Số vị trí giống câu hỏi tìm được:", len(starts))

    rows = []

    for i, match in enumerate(starts):
        qid = int(match.group(1))

        # Chỉ lấy câu hỏi thật từ 1 đến 100 cho an toàn
        if qid < 1 or qid > 100:
            continue

        start = match.start()
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)

        chunk = clean_text(text[start:end])

        row = parse_question(qid, chunk)

        # Chỉ giữ những câu có ít nhất nội dung câu hỏi
        if row["question"]:
            rows.append(row)

    df = pd.DataFrame(rows)

    # Xóa câu trùng qid, giữ bản đầu tiên
    df = df.drop_duplicates(subset=["qid"], keep="first")

    # Sắp xếp theo qid
    df = df.sort_values("qid")

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"Đã tạo file: {OUTPUT_CSV}")
    print(f"Số câu tách được: {len(df)}")

    blank_options = df[
        (df["A"] == "") |
        (df["B"] == "") |
        (df["C"] == "") |
        (df["D"] == "")
    ]

    print(f"Số câu chưa tách đủ A/B/C/D: {len(blank_options)}")

    print("\nXem thử 10 câu đầu:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    convert_docx_to_csv()