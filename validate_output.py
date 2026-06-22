"""
Script kiểm tra nhanh file pred.csv trước khi nộp bài, KHÔNG cần model/GPU.

Cách dùng:
    python validate_output.py /duong/dan/toi/pred.csv [so_cau_ky_vong]
"""

import sys
import pandas as pd


def main():
    if len(sys.argv) < 2:
        print("Cách dùng: python validate_output.py <duong_dan_pred.csv> [so_cau_ky_vong]")
        sys.exit(1)

    path = sys.argv[1]
    expected = int(sys.argv[2]) if len(sys.argv) > 2 else None

    df = pd.read_csv(path)
    ok = True

    if list(df.columns) != ["qid", "answer"]:
        print(f"[LỖI] Cột phải đúng là ['qid', 'answer'], hiện tại: {list(df.columns)}")
        ok = False

    if expected is not None and len(df) != expected:
        print(f"[LỖI] Số dòng = {len(df)}, kỳ vọng = {expected}")
        ok = False

    if "qid" in df.columns and df["qid"].duplicated().any():
        print("[LỖI] Có qid bị trùng.")
        ok = False

    if "answer" in df.columns:
        invalid = ~df["answer"].astype(str).str.upper().isin(["A", "B", "C", "D"])
        if invalid.any():
            print(f"[LỖI] {invalid.sum()} dòng có đáp án không thuộc A/B/C/D.")
            ok = False

    if df.isna().any().any():
        print("[LỖI] Có giá trị rỗng (NaN) trong file.")
        ok = False

    if ok:
        print(f"[OK] File {path} hợp lệ - {len(df)} dòng, không lỗi.")
    else:
        print(f"[THẤT BẠI] File {path} có vấn đề, xem chi tiết phía trên.")
        sys.exit(1)


if __name__ == "__main__":
    main()
