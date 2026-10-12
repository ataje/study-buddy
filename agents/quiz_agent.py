import math

from llm import LLMService


class QuizAgent:
    def __init__(self, llm_service=None, model_name=None):
        self.llm_service = llm_service or LLMService(model_name=model_name, default_temperature=0.3)

    def generate_quiz(self, retrieved_chunks, num_questions=3):
        context = "\n\n".join(retrieved_chunks[:5])

        system_prompt = """
You are a quiz-writing tutor for a study assistant called Study Buddy.
You create short, clear quizzes based only on the provided lecture context.
Return valid JSON only.
"""

        user_prompt = f"""
Create a quiz with exactly {num_questions} questions based only on the lecture context below.

Requirements:
- Return JSON with this exact top-level shape:
{{
  "title": "short quiz title",
  "questions": [
    {{
      "question": "question text",
      "type": "short_answer or multiple_choice",
      "options": ["A", "B", "C", "D"],
      "answer": "correct answer",
      "explanation": "brief explanation"
    }}
  ]
}}
- Include a mix of short_answer and multiple_choice when possible.
- For multiple_choice, answer must match one option exactly, not just its letter.
- For short_answer questions, use an empty list for "options".
- Use only facts supported by the lecture context.
- Keep wording student-friendly and concise.

Lecture Context:
{context}
"""

        result = self.llm_service.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        return self.validate_quiz(result, num_questions)

    @staticmethod
    def validate_quiz(result, num_questions=3):
        message = "The AI returned an incomplete quiz. Please generate another quiz."
        questions = result.get("questions")
        if not isinstance(result.get("title"), str) or not result["title"].strip():
            raise ValueError(message)
        if not isinstance(questions, list) or len(questions) != num_questions:
            raise ValueError(message)
        for question in questions:
            if not isinstance(question, dict):
                raise ValueError(message)
            for key in ("question", "answer", "explanation"):
                if not isinstance(question.get(key), str) or not question[key].strip():
                    raise ValueError(message)
            if question.get("type") not in {"multiple_choice", "short_answer"}:
                raise ValueError(message)
            options = question.get("options")
            if not isinstance(options, list):
                raise ValueError(message)
            if question["type"] == "multiple_choice":
                if not 2 <= len(options) <= 6 or any(not isinstance(x, str) or not x.strip() for x in options):
                    raise ValueError(message)
                if len(set(options)) != len(options) or question["answer"] not in options:
                    raise ValueError(message)
            elif options:
                raise ValueError(message)
        return result

    def check_answer(self, question, student_answer):
        question_type = question.get("type", "short_answer")
        correct_answer = (question.get("answer") or "").strip()
        explanation = question.get("explanation", "")
        student_answer = (student_answer or "").strip()

        if not student_answer:
            return {
                "is_correct": False,
                "score": 0.0,
                "feedback": "No answer was submitted yet.",
                "correct_answer": correct_answer,
                "explanation": explanation,
            }

        if question_type == "multiple_choice":
            is_correct = student_answer.lower() == correct_answer.lower()
            return {
                "is_correct": is_correct,
                "score": 1.0 if is_correct else 0.0,
                "feedback": "Correct." if is_correct else "Not quite. Try comparing your choice to the key idea in the lecture.",
                "correct_answer": correct_answer,
                "explanation": explanation,
            }

        system_prompt = """
You are grading a student's short-answer quiz response.
Judge whether the student's answer is correct based on the target answer and explanation.
Be fair about wording differences, but do not accept answers that change the meaning.
Return valid JSON only.
"""

        user_prompt = f"""
Evaluate this student answer.

Return JSON with this exact shape:
{{
  "is_correct": true,
  "score": 1.0,
  "feedback": "one or two sentence feedback"
}}

Question:
{question.get("question", "")}

Correct answer:
{correct_answer}

Reference explanation:
{explanation}

Student answer:
{student_answer}
"""

        result = self.llm_service.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0,
        )

        score = float(result.get("score", 0.0))
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("The grader returned an invalid score. Please try again.")
        if not isinstance(result.get("is_correct"), bool):
            raise ValueError("The grader returned an invalid result. Please try again.")
        return {
            "is_correct": result["is_correct"],
            "score": score,
            "feedback": result.get("feedback", "Feedback unavailable."),
            "correct_answer": correct_answer,
            "explanation": explanation,
        }
