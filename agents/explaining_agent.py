from llm import LLMService


class ExplainingAgent:
    def __init__(self, llm_service=None, model_name=None):
        self.llm_service = llm_service or LLMService(model_name=model_name, default_temperature=0.4)

    def generate_full_lesson(self, retrieved_chunks):
        context = "\n\n".join(retrieved_chunks[:5])

        system_prompt = """
You are a patient, encouraging professor teaching a student from lecture slides.
"""

        user_prompt = f"""
You are a patient, encouraging professor teaching a student from lecture slides.

Your job:
- Explain the concepts supported by the provided excerpts; do not claim complete lecture coverage
- Cite the supplied page labels when explaining a claim
- If an idea is missing from the context, say so
- Start naturally like a teacher
- Identify the main topic from the lecture context
- Explain the material in a clear order from basic ideas to more detailed ideas
- Keep it structured and easy to follow
- Do not mention "chunks" or "retrieval"
- Do not dump raw notes
- Sound like a professor teaching a student step by step

Lecture Context:
{context}

Please format the lesson like this:
1. Title of today's topic
2. Short introduction
3. Main ideas explained clearly
4. Why this topic matters
5. A short recap at the end

Start with a concise topic heading. Avoid unnecessary greetings.
"""

        return self.llm_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
        )

    def answer_followup(self, question, retrieved_chunks):
        context = "\n\n".join(retrieved_chunks[:5])

        system_prompt = """
You are a helpful professor answering a student's follow-up question about a lecture.
"""

        user_prompt = f"""
You are a helpful professor answering a student's follow-up question about a lecture.

Rules:
- Use only the lecture context below
- Be clear, warm, and direct
- Answer like a teacher, not like a chatbot
- If the lecture does not clearly contain the answer, say so honestly

Student question:
{question}

Lecture Context:
{context}
"""
        return self.llm_service.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )
