"""
LLM client cho bài thi.

Chỉ còn 2 chế độ:
- LLM_MODE=dummy: test nhanh pipeline, KHÔNG dùng để nộp.
- LLM_MODE=gguf : chạy LLM local bằng llama.cpp + model GGUF, KHÔNG gọi AI ngoài.
"""

import os


class LLMClient:
    def __init__(self):
        self.mode = os.environ.get("LLM_MODE", "gguf").lower().strip()

        # Model mặc định: có thể đổi bằng biến môi trường khi chạy.
        self.gguf_repo = os.environ.get("GGUF_REPO", "unsloth/Qwen3.5-4B-GGUF")
        self.gguf_filename = os.environ.get("GGUF_FILENAME", "*Q4_K_M*")
        self.n_ctx = int(os.environ.get("N_CTX", "4096"))
        self.n_threads = int(os.environ.get("N_THREADS", str(os.cpu_count() or 4)))
        self.max_tokens = int(os.environ.get("MAX_TOKENS", "12"))

        self._llama = None

        if self.mode == "dummy":
            print("[LLMClient] LLM_MODE=dummy: chỉ test pipeline, chưa dùng LLM thật.")
        elif self.mode == "gguf":
            self._load_gguf_model()
        else:
            raise ValueError(
                f"LLM_MODE không hợp lệ: '{self.mode}'. Chỉ nhận 'dummy' hoặc 'gguf'."
            )

    def _load_gguf_model(self):
        from llama_cpp import Llama

        print(
            f"[LLMClient] Đang tải GGUF local: repo={self.gguf_repo}, "
            f"file={self.gguf_filename}, ctx={self.n_ctx}, threads={self.n_threads}"
        )

        self._llama = Llama.from_pretrained(
            repo_id=self.gguf_repo,
            filename=self.gguf_filename,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            verbose=False,
        )
        print("[LLMClient] Tải model GGUF xong.")

    def ask(self, prompt: str) -> str:
        if self.mode == "dummy":
            return self._ask_dummy(prompt)
        return self._ask_gguf(prompt)

    def _ask_dummy(self, prompt: str) -> str:
        """Test nhanh, không dùng để nộp."""
        text = prompt.lower()
        if "python" in text and "ngôn ngữ lập trình" in text:
            return "B"
        if "tcp/ip" in text and "định tuyến" in text:
            return "B"
        # fallback cố định để đảm bảo pred.csv luôn đúng format
        return "A"

    def _ask_gguf(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a multiple-choice exam solver. "
                    "Return exactly one letter: A, B, C, or D. "
                    "No explanation."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = self._llama.create_chat_completion(
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=0.0,
        )
        return response["choices"][0]["message"]["content"].strip()
