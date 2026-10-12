from llm import LLMService


class ResponseReviewAgent:
    def __init__(self, llm_service=None, model_name=None):
        self.llm_service = llm_service or LLMService(model_name=model_name, default_temperature=0.1)

    def review_explanation(self, user_query, draft_response, retrieved_chunks):
        cleaned_draft = (draft_response or "").strip()
        if not cleaned_draft:
            return {
                "final_response": "",
                "approved": False,
                "notes": "No draft response was available to review.",
            }

        if not self.llm_service.is_configured():
            return {
                "final_response": cleaned_draft,
                "approved": False,
                "notes": "This draft has not been reviewed; live AI is unavailable.",
            }

        context = "\n\n".join((retrieved_chunks or [])[:5])

        system_prompt = """
You are a response review agent for a tutoring app called Study Buddy.

Your job is to review a draft explanation before it is shown to the student.

Return valid JSON only with this exact shape:
{
  "final_response": "revised response",
  "approved": true,
  "notes": "brief review note"
}

Rules:
- Keep the answer grounded in the lecture context.
- Remove unsupported claims.
- Keep the tone warm, direct, and teacher-like.
- Improve clarity if needed, but do not add outside facts that are not supported by the context.
"""

        user_prompt = f"""
Student request:
{user_query}

Lecture context:
{context}

Draft response:
{cleaned_draft}
"""

        try:
            result = self.llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0,
            )
        except Exception:
            return {
                "final_response": cleaned_draft,
                "approved": False,
                "notes": "This draft has not been reviewed; the review request failed.",
            }

        candidate = result.get("final_response")
        if not isinstance(candidate, str) or not candidate.strip():
            return {"final_response": cleaned_draft, "approved": False,
                    "notes": "This draft has not been reviewed; the review response was invalid."}
        final_response = candidate.strip()
        return {
            "final_response": final_response,
            "approved": result.get("approved") is True,
            "notes": result.get("notes", "Reviewed for grounding and clarity."),
        }
