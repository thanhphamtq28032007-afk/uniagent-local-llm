# Local LLM Multiple Choice Solver

Dự án đọc `/data/private_test.csv` hoặc `/data/public_test.csv`, dùng LLM local để chọn đáp án A/B/C/D, rồi xuất `/output/pred.csv`.

## Chế độ chạy

- `LLM_MODE=dummy`: test pipeline, không dùng AI thật.
- `LLM_MODE=gguf`: chạy LLM local bằng llama.cpp + GGUF. Không gọi API ngoài.

## Test nhanh trên Windows PowerShell

```powershell
$env:DATA_DIR=".\data"
$env:OUTPUT_DIR=".\output"
$env:LLM_MODE="dummy"
python main.py
type output/pred.csv
```

## Chạy LLM local GGUF

Lần đầu cần internet để tải model GGUF về máy. Sau khi tải xong, model chạy local.

```powershell
$env:DATA_DIR=".\data"
$env:OUTPUT_DIR=".\output"
$env:LLM_MODE="gguf"
$env:GGUF_REPO="unsloth/Qwen3.5-4B-GGUF"
$env:GGUF_FILENAME="*Q4_K_M*"
$env:N_THREADS="4"
$env:N_CTX="4096"
$env:MAX_TOKENS="12"
python main.py
type output/pred.csv
```

## Docker

```bash
docker build -t local-llm-solver .
docker run --rm -v /path/to/data:/data -v /path/to/output:/output local-llm-solver
```

Kết quả phải có dạng:

```csv
qid,answer
1,A
2,C
```
