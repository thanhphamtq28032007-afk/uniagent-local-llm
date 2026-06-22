# Tài liệu thuyết minh phương pháp

## 1. Tổng quan giải pháp

Hệ thống được xây dựng để giải bài toán trắc nghiệm A/B/C/D bằng mô hình ngôn ngữ lớn chạy cục bộ. Chương trình tự động đọc file câu hỏi từ thư mục `/data`, xử lý từng câu hỏi, sinh đáp án bằng LLM local và ghi kết quả ra `/output/pred.csv`.

Toàn bộ quá trình inference được thực hiện trong Docker container. Hệ thống không sử dụng API AI bên ngoài trong quá trình chấm điểm.

Luồng xử lý chính:

```text
/data/public_test.csv hoặc /data/private_test.csv
        ↓
Đọc dữ liệu câu hỏi
        ↓
Chuẩn hóa câu hỏi và các lựa chọn A/B/C/D
        ↓
Tạo prompt cho LLM local
        ↓
Sinh đáp án
        ↓
Chuẩn hóa output về A/B/C/D
        ↓
Ghi /output/pred.csv
```

## 2. Lựa chọn model

Model sử dụng trong bản hiện tại là mô hình ngôn ngữ lớn dạng GGUF, chạy thông qua `llama.cpp` bằng thư viện `llama-cpp-python`.

Cấu hình mặc định:

```text
LLM_MODE=gguf
GGUF_REPO=unsloth/Qwen3.5-4B-GGUF
GGUF_FILENAME=*Q4_K_M*
```

Lý do chọn hướng GGUF:

* Không cần gọi API AI bên ngoài.
* Có thể chạy local trong Docker container.
* Phù hợp hơn với môi trường tài nguyên hạn chế so với việc chạy model gốc bằng `transformers`.
* Quantization giúp giảm dung lượng model và giảm yêu cầu RAM.
* Vẫn giữ được chất lượng suy luận đủ tốt cho bài toán trắc nghiệm A/B/C/D.

Trong quá trình phát triển, hệ thống cũng hỗ trợ chế độ `dummy` để kiểm tra pipeline đọc file, xử lý dữ liệu và ghi kết quả. Chế độ này chỉ dùng để kiểm thử kỹ thuật, không dùng cho bản chấm chính thức.

## 3. Chiến lược prompt

Mỗi câu hỏi được chuyển thành prompt có cấu trúc rõ ràng gồm:

* Nội dung câu hỏi.
* Phương án A.
* Phương án B.
* Phương án C.
* Phương án D.
* Yêu cầu mô hình chỉ trả về một ký tự duy nhất: A, B, C hoặc D.

Mục tiêu của prompt là giảm khả năng mô hình trả lời dài dòng hoặc sinh thêm giải thích không cần thiết.

Ví dụ cấu trúc prompt:

```text
Bạn là AI chuyên giải câu hỏi trắc nghiệm A/B/C/D.
Hãy đọc câu hỏi, so sánh các phương án và chọn đáp án đúng nhất.
Chỉ trả về duy nhất một ký tự: A, B, C hoặc D.

Câu hỏi:
...

A. ...
B. ...
C. ...
D. ...

Đáp án:
```

Chiến lược này giúp đầu ra ổn định hơn và thuận tiện cho việc ghi kết quả vào file `pred.csv`.

## 4. Xử lý và chuẩn hóa đầu ra

Vì LLM đôi khi có thể trả lời nhiều hơn một ký tự, hệ thống có module chuẩn hóa đáp án trong `utils.py`.

Ví dụ các đầu ra như:

```text
Answer: B
Đáp án là C
I choose D
B.
```

đều được chuyển về đúng định dạng:

```text
B
C
D
B
```

Nếu mô hình không trả về được đáp án hợp lệ, hệ thống có cơ chế fallback để đảm bảo mỗi câu hỏi luôn có một đáp án thuộc tập A/B/C/D. Điều này giúp file `pred.csv` luôn đúng định dạng yêu cầu.

## 5. RAG

Hệ thống hiện tại không sử dụng RAG trong bản chạy chính.

Lý do:

* Dữ liệu chấm là câu hỏi trắc nghiệm tổng quát, không có corpus tài liệu chính thức đi kèm.
* Việc thêm RAG khi không có nguồn tri thức chuẩn có thể làm tăng thời gian inference mà chưa chắc cải thiện accuracy.
* Bài toán ưu tiên độ ổn định, tốc độ và khả năng chạy được trong Docker.

Do đó, nhóm lựa chọn hướng dùng LLM local kết hợp prompt tối ưu và chuẩn hóa output.

## 6. Tối ưu tốc độ inference

Các kỹ thuật tối ưu đã áp dụng:

* Sử dụng model dạng GGUF đã quantize để giảm dung lượng và giảm yêu cầu bộ nhớ.
* Dùng `llama.cpp` thông qua `llama-cpp-python` để chạy inference local.
* Giới hạn số token sinh ra vì bài toán chỉ cần đáp án A/B/C/D.
* Cấu hình `MAX_TOKENS` nhỏ để tránh mô hình sinh câu trả lời dài.
* Cấu hình `N_THREADS` để tận dụng CPU khi chạy local.
* Không bật cơ chế self-check nhiều lượt nhằm tránh tăng thời gian xử lý mỗi câu.

Cấu hình mặc định:

```text
N_THREADS=4
N_CTX=4096
MAX_TOKENS=12
```

Các tham số này có thể điều chỉnh tùy môi trường chạy thực tế.

## 7. Input và Output

Hệ thống tự động tìm file đầu vào trong thư mục `/data`.

Các tên file được hỗ trợ:

```text
/data/private_test.csv
/data/public_test.csv
/data/test.csv
```

Khi chạy local, hệ thống cũng hỗ trợ:

```text
data/private_test.csv
data/public_test.csv
data/test.csv
```

File đầu vào nên có cấu trúc:

```csv
qid,question,A,B,C,D
1,"Nội dung câu hỏi","Đáp án A","Đáp án B","Đáp án C","Đáp án D"
```

File đầu ra được ghi tại:

```text
/output/pred.csv
```

Định dạng đầu ra:

```csv
qid,answer
1,A
2,C
3,B
```

## 8. Docker

Dự án được đóng gói bằng Docker để đảm bảo khả năng tái lập.

Quy trình chạy trong Docker:

```text
1. Container khởi động.
2. Chương trình tìm file CSV trong /data.
3. LLM local được khởi tạo.
4. Từng câu hỏi được xử lý.
5. Kết quả được ghi vào /output/pred.csv.
```

Lệnh build image:

```bash
docker build -t uniagent-local-llm:v1 .
```

Lệnh chạy mẫu:

```bash
docker run --rm \
-v ./data:/data \
-v ./output:/output \
-e DATA_DIR=/data \
-e OUTPUT_DIR=/output \
-e LLM_MODE=gguf \
-e GGUF_REPO=unsloth/Qwen3.5-4B-GGUF \
-e GGUF_FILENAME="*Q4_K_M*" \
-e N_THREADS=4 \
-e N_CTX=4096 \
-e MAX_TOKENS=12 \
uniagent-local-llm:v1
```

## 9. Kết quả thực nghiệm

Bảng dưới đây sẽ được cập nhật sau khi chạy kiểm thử trên bộ public/private test chính thức.

| Chỉ số                   | Giá trị                              |
| ------------------------ | ------------------------------------ |
| Số câu test              | Cập nhật sau khi chạy                |
| Accuracy                 | Cập nhật sau khi có đáp án đối chiếu |
| Tổng thời gian chạy      | Cập nhật sau khi chạy Docker         |
| Thời gian trung bình/câu | Cập nhật sau khi chạy Docker         |

Nhóm không tự ghi accuracy khi chưa có đáp án chuẩn để đối chiếu, nhằm đảm bảo tính trung thực của báo cáo.

## 10. Hạn chế và hướng cải thiện

Một số hạn chế hiện tại:

* Model local dạng GGUF có thể chậm hơn khi chạy trên CPU so với môi trường GPU.
* Chất lượng trả lời phụ thuộc vào model GGUF được chọn.
* Với câu hỏi quá dài hoặc nhiều ngữ cảnh, model nhỏ có thể suy luận chưa ổn định.
* Hệ thống chưa sử dụng RAG vì chưa có corpus chính thức từ Ban Tổ chức.

Hướng cải thiện:

* Thử nghiệm model lớn hơn trong giới hạn cho phép nếu môi trường chạy đủ mạnh.
* Tối ưu prompt cho từng nhóm câu hỏi.
* Thử các mức quantization khác nhau để cân bằng giữa accuracy và tốc độ.
* Bổ sung cơ chế kiểm tra lại đáp án cho các câu hỏi có độ không chắc chắn cao.
