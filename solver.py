"""
Solver: nhận câu hỏi trắc nghiệm, gọi LLM local, trả về đúng 1 chữ cái A/B/C/D.
"""

from llm_client import LLMClient
from utils import extract_answer


class MultipleChoiceSolver:
    def __init__(self):
        self.llm = LLMClient()

    def solve(self, question_text: str) -> str:
        prompt = self.build_prompt(question_text)
        raw_answer = self.llm.ask(prompt)

        answer = extract_answer(raw_answer, default=None)
        if answer in ["A", "B", "C", "D"]:
            return answer

        # Retry nhẹ nếu model trả lời không rõ format.
        retry_prompt = self.build_retry_prompt(question_text, raw_answer)
        retry_answer = self.llm.ask(retry_prompt)
        return extract_answer(retry_answer, default="A")

    @staticmethod
    def build_prompt(question_text: str) -> str:
        return f"""
Read the multiple-choice question carefully.
Compare options A, B, C, and D.
Choose the best answer.

STRICT OUTPUT RULES:
- Output exactly one character only: A, B, C, or D.
- Do not explain.
- Do not write words like "Answer" or "Đáp án".
- Do not add punctuation.

Question:
{question_text}

Final answer:
""".strip()

    @staticmethod
    def build_retry_prompt(question_text: str, previous_output: str) -> str:
        return f"""
Your previous output was not in the required format.
Now answer again.

Question:
{question_text}

Previous output:
{previous_output}

Return exactly one letter only: A, B, C, or D.
""".strip()
