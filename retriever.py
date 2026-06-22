"""
Module retrieval TÙY CHỌN, dùng BGE-m3 (embedding) + reranker kiểu Qwen-Rerank.

Chỉ dùng khi USE_RAG=true. Đặt các file văn bản (.txt) của corpus/tài liệu
tham khảo vào KB_DIR trước khi bật tính năng này.

Đây là bản tìm kiếm brute-force trong RAM - phù hợp corpus vài nghìn đoạn
văn. Nếu corpus lớn hơn, nên thay bằng vector index thật (ví dụ FAISS).
"""

import os
import glob
import numpy as np
from FlagEmbedding import BGEM3FlagModel, FlagReranker

KB_DIR = os.environ.get("KB_DIR", "/data/knowledge_base")
TOP_K_RETRIEVE = 10
TOP_K_RERANK = 3


class Retriever:
    def __init__(self):
        self.embedder = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

        # NOTE: đổi sang checkpoint Qwen-Rerank chính thức nếu BTC yêu cầu
        # đúng tên model đó; dùng tạm bge-reranker-v2-m3 để code chạy được.
        self.reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)

        self.passages = self._load_corpus()
        self.passage_embeddings = self._embed_passages(self.passages)

    def _load_corpus(self):
        passages = []
        for path in glob.glob(os.path.join(KB_DIR, "*.txt")):
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for chunk in text.split("\n\n"):
                chunk = chunk.strip()
                if chunk:
                    passages.append(chunk)
        return passages

    def _embed_passages(self, passages):
        if not passages:
            return np.zeros((0, 1024))
        out = self.embedder.encode(passages)["dense_vecs"]
        return np.array(out)

    def retrieve(self, question):
        if not self.passages:
            return None

        q_emb = self.embedder.encode([question])["dense_vecs"][0]
        scores = self.passage_embeddings @ q_emb
        top_idx = np.argsort(scores)[::-1][:TOP_K_RETRIEVE]
        candidates = [self.passages[i] for i in top_idx]

        pairs = [[question, c] for c in candidates]
        rerank_scores = self.reranker.compute_score(pairs)
        ranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)

        best_passages = [p for p, _ in ranked[:TOP_K_RERANK]]
        return "\n---\n".join(best_passages)
