"""
Tiện ích: tìm/đọc CSV, ghép câu hỏi + đáp án, lọc đáp án A/B/C/D.
"""

import os
import re
import glob
import pandas as pd

ID_COL_CANDIDATES = ["qid", "id", "question_id", "ID", "QID"]
QUESTION_COL_CANDIDATES = ["question", "Question", "cau_hoi", "Câu hỏi", "prompt"]
OPTION_COLS = ["A", "B", "C", "D"]


def find_input_file(data_dir: str) -> str:
    private = glob.glob(os.path.join(data_dir, "private_test.csv"))
    if private:
        return private[0]

    public = glob.glob(os.path.join(data_dir, "public_test.csv"))
    if public:
        return public[0]

    raise FileNotFoundError(
        f"Không tìm thấy private_test.csv hoặc public_test.csv trong {data_dir}"
    )


def read_input_csv(input_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise RuntimeError(f"Không đọc được file CSV: {e}")

    if df.empty:
        raise RuntimeError(f"File {input_path} không có dữ liệu.")

    return df


def get_question_id(row, index: int):
    for col in ID_COL_CANDIDATES:
        if col in row.index:
            return row[col]
    return index + 1


def _clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _clean_option_text(opt_letter: str, raw_value) -> str:
    text = _clean_text(raw_value)
    prefix_pattern = re.compile(rf"^{re.escape(opt_letter)}\s*[\.\):]\s*", re.IGNORECASE)
    return prefix_pattern.sub("", text).strip()


def build_question_text(row) -> str:
    question_text = ""
    for col in QUESTION_COL_CANDIDATES:
        if col in row.index:
            question_text = _clean_text(row[col])
            break

    if not question_text:
        parts = [f"{col}: {_clean_text(row[col])}" for col in row.index]
        question_text = "\n".join(parts)

    if all(col in row.index for col in OPTION_COLS):
        options = []
        for opt in OPTION_COLS:
            value = _clean_option_text(opt, row[opt])
            if value:
                options.append(f"{opt}. {value}")
        if options:
            question_text += "\n" + "\n".join(options)

    return question_text.strip()


def extract_answer(text: str, default="A"):
    """
    Trích A/B/C/D từ output của LLM.
    Nếu default=None và không tìm thấy đáp án rõ ràng, trả về None.
    """
    if text is None:
        return default

    original = str(text).strip()
    if not original:
        return default

    upper = original.upper().strip()

    # Output sạch đúng 1 chữ cái.
    if upper in ["A", "B", "C", "D"]:
        return upper

    patterns = [
        r"(?:FINAL\s+ANSWER|ANSWER|ĐÁP\s*ÁN|CHỌN)\s*[:\-]?\s*([ABCD])\b",
        r"\bOPTION\s*([ABCD])\b",
        r"\b([ABCD])\s*(?:IS\s+CORRECT|IS\s+THE\s+ANSWER)\b",
        r"^\s*([ABCD])\s*[\).:\-]",
    ]

    for pattern in patterns:
        match = re.search(pattern, upper, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()

    # Chỉ fallback theo chữ cái đơn lẻ nếu có đúng 1 chữ cái A-D xuất hiện.
    letters = re.findall(r"\b([ABCD])\b", upper)
    unique_letters = sorted(set(letters))
    if len(unique_letters) == 1:
        return unique_letters[0]

    return default


def validate_predictions(df: pd.DataFrame, expected_rows: int) -> list:
    issues = []

    if len(df) != expected_rows:
        issues.append(
            f"Số dòng kết quả ({len(df)}) khác số câu hỏi đầu vào ({expected_rows})."
        )

    if df["qid"].duplicated().any():
        issues.append("Có qid bị trùng trong kết quả.")

    invalid = ~df["answer"].astype(str).str.upper().isin(["A", "B", "C", "D"])
    if invalid.any():
        issues.append(f"Có {invalid.sum()} dòng đáp án không thuộc A/B/C/D.")

    if df["answer"].isna().any():
        issues.append("Có dòng đáp án bị rỗng (NaN).")

    return issues
