"""
Entry-point chính cho cuộc thi (Vòng 1 - Bảng C Innovator).

Hành vi:
    - Đọc câu hỏi từ /data/private_test.csv (ưu tiên) hoặc /data/public_test.csv
    - Với mỗi câu, gọi LLM để chọn đáp án A/B/C/D
    - Ghi kết quả vào /output/pred.csv với 2 cột: qid,answer
    - Nếu 1 câu bị lỗi giữa đường (model lag, lỗi parse...), KHÔNG dừng
      toàn bộ chương trình - chỉ log lỗi và gán tạm "A" cho câu đó, để vẫn
      ra đủ file kết quả cho các câu còn lại.
    - Nếu quá nửa số câu bị lỗi -> in cảnh báo nghiêm trọng (rất có thể
      model/API chưa cấu hình đúng).
"""

import os
import sys
import pandas as pd

from utils import read_input_csv, find_input_file, get_question_id, build_question_text, validate_predictions
from solver import MultipleChoiceSolver


def main():
    data_dir = os.environ.get("DATA_DIR", "/data")
    output_dir = os.environ.get("OUTPUT_DIR", "/output")

    try:
        input_path = find_input_file(data_dir)
    except FileNotFoundError as e:
        print(f"[LỖI] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Đang đọc file đầu vào: {input_path}")
    df = read_input_csv(input_path)

    try:
        solver = MultipleChoiceSolver()
    except Exception as e:
        print(f"[LỖI] Không khởi tạo được solver/LLM: {e}", file=sys.stderr)
        sys.exit(1)

    results = []
    errors = 0
    total = len(df)

    for index, row in df.iterrows():
        qid = get_question_id(row, index)
        question_text = build_question_text(row)
        print(f"[{index + 1}/{total}] Đang xử lý câu {qid}...")

        try:
            answer = solver.solve(question_text)
        except Exception as e:
            print(f"[LỖI] Câu {qid} thất bại: {type(e).__name__}: {e}", file=sys.stderr)
            answer = "A"
            errors += 1

        results.append({"qid": qid, "answer": answer})

    if total > 0 and errors / total > 0.5:
        print(
            f"[CẢNH BÁO NGHIÊM TRỌNG] {errors}/{total} câu bị lỗi khi gọi LLM (>50%). "
            "Rất có thể model/API chưa được cấu hình đúng. Kiểm tra lại trước khi nộp bài.",
            file=sys.stderr,
        )

    result_df = pd.DataFrame(results)

    for issue in validate_predictions(result_df, expected_rows=total):
        print(f"[CẢNH BÁO] {issue}", file=sys.stderr)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "pred.csv")
    result_df.to_csv(output_path, index=False)

    print(f"Đã xuất {len(result_df)} dòng kết quả ra: {output_path} ({errors} câu bị lỗi).")


if __name__ == "__main__":
    main()