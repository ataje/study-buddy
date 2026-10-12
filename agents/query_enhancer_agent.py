from llm import LLMService


class QueryEnhancerAgent:
    def __init__(self, llm_service=None, model_name=None):
        self.llm_service = llm_service or LLMService(model_name=model_name, default_temperature=0.2)

    def enhance_query(self, user_query, document_preview="", intent="general"):
        cleaned_query = (user_query or "").strip()
        if not cleaned_query:
            return {
                "enhanced_query": "",
                "retrieval_query": "",
                "response_goal": "clarify",
                "needs_clarification": True,
                "clarification_question": "What topic from your lecture would you like help with?",
            }

        if not self.llm_service.is_configured():
            return self._fallback_enhancement(cleaned_query, intent)

        system_prompt = """
You are a query enhancement agent inside a tutoring app called Study Buddy.

Your job is to rewrite a student's request so the retrieval system can search a lecture document more effectively.

Return valid JSON only with this exact shape:
{
  "enhanced_query": "clean student-friendly rewrite",
  "retrieval_query": "specific search query for vector retrieval",
  "response_goal": "explain | summarize | quiz | retrieve | navigate | clarify",
  "needs_clarification": false,
  "clarification_question": null
}

Rules:
- Preserve the student's meaning.
- Make the retrieval_query short, concrete, and focused on lecture concepts.
- If the question is vague, create the best retrieval query you can.
- Only set needs_clarification to true if the request is too underspecified to act on at all.
"""

        user_prompt = f"""
Student request:
{cleaned_query}

Inferred intent:
{intent}

Document preview:
{document_preview[:1200]}
"""

        try:
            result = self.llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0,
            )
        except Exception:
            return self._fallback_enhancement(cleaned_query, intent)

        return {
            "enhanced_query": (result.get("enhanced_query") or cleaned_query).strip(),
            "retrieval_query": (result.get("retrieval_query") or cleaned_query).strip(),
            "response_goal": result.get("response_goal", intent or "general"),
            "needs_clarification": bool(result.get("needs_clarification", False)),
            "clarification_question": result.get("clarification_question"),
        }

    def _fallback_enhancement(self, user_query, intent):
        intent = intent or "general"
        prefix_map = {
            "quiz": "key concepts, definitions, and practice questions about",
            "summarize": "summary of",
            "retrieve": "lecture section about",
            "navigate": "next section after",
            "explain": "clear explanation of",
            "general": "important lecture ideas about",
        }
        prefix = prefix_map.get(intent, prefix_map["general"])
        retrieval_query = f"{prefix} {user_query}".strip()
        return {
            "enhanced_query": user_query,
            "retrieval_query": retrieval_query,
            "response_goal": intent,
            "needs_clarification": False,
            "clarification_question": None,
        }
