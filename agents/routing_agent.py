from llm import LLMService
from llm.budget import UsageLimitError
from llm.service import ProviderError


class RoutingAgent:
    def __init__(self, llm_service=None, model_name=None):
        self.llm_service = llm_service or LLMService(model_name=model_name, default_temperature=0)

    def route_mode(self, mode):
        """
        Simple router for homepage buttons.
        """
        if mode == "study":
            return "explaining"
        elif mode == "practice":
            return "quiz"
        elif mode == "other":
            return "other"
        return None

    def llm_router_decision(self, user_query: str, has_document: bool, doc_context=None, app_state=None):
        """
        LLM-based router for natural language requests.
        """
        if not has_document:
            return {
                "selected_agent": "clarification_agent", "intent": "missing_document",
                "confidence": 1.0, "needs_clarification": True,
                "reasoning": "A lecture is needed before a document-based request.",
                "clarification_question": "Choose Study or Practice and prepare a lecture PDF first.",
            }

        if not self.llm_service.is_configured():
            return {
                "selected_agent": "clarification_agent",
                "intent": "missing_llm_config",
                "confidence": 0.0,
                "reasoning": "The shared LLM service is not configured.",
                "needs_clarification": True,
                "clarification_question": "The smart routing model is not configured yet."
            }

        if doc_context is None:
            doc_context = {"summary_preview": "", "candidate_headings": []}

        if app_state is None:
            app_state = {
                "current_section": None,
                "mode": "teaching"
            }

        system_prompt = """
You are the deciding/routing agent in a multi-agent tutoring system called Study Buddy.

Your job is to select the BEST next agent for the user's request.

Available agents:
1. query_enhancer
   - Use when the user's request is explain-like but vague or needs rewriting before retrieval.
2. retrieval_agent
   - Use when the system should search the uploaded document for a topic, section, slide, or relevant context.
3. explaining_agent
   - Use when enough context already exists and the user directly wants an explanation.
4. quiz_agent
   - Use when the user wants to be tested, practice questions, or quiz mode.
5. navigation_agent
   - Use when the user wants to move to next/previous section or continue the lesson flow.
6. clarification_agent
   - Use when the request is too unclear or more detail is required.

Rules:
- If no document is uploaded and the request depends on uploaded material, choose clarification_agent.
- If the user asks for explanation but does not specify a topic, section, page, or slide, clarification_agent is acceptable.
- If the user asks for explanation of a topic that likely needs better phrasing for retrieval, choose query_enhancer.
- If the user asks to continue or move ahead, choose navigation_agent.
- If the user asks for summary or to find a section, choose retrieval_agent first.
- If the user asks for a quiz, test, or practice questions, choose quiz_agent.
- Prefer clarification_agent when confidence is low.

Select exactly one of the six agent names listed above. Return ONLY valid JSON in this format:
{
  "selected_agent": "explaining_agent",
  "intent": "short_intent_label",
  "confidence": 0.0,
  "reasoning": "brief reasoning",
  "needs_clarification": true,
  "clarification_question": "question or null"
}
"""

        user_prompt = f"""
User query:
{user_query}

Has uploaded document:
{has_document}

Document summary preview:
{doc_context.get("summary_preview", "")}

Candidate headings:
{doc_context.get("candidate_headings", [])}

Current app state:
{app_state}
"""

        try:
            result = self.llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0,
            )
            allowed = {"query_enhancer", "retrieval_agent", "explaining_agent", "quiz_agent",
                       "navigation_agent", "clarification_agent"}
            if result.get("selected_agent") not in allowed:
                raise ValueError("Unexpected route")
            return result

        except Exception as exc:
            message = str(exc) if isinstance(exc, (UsageLimitError, ProviderError)) else "This request could not be completed. Please try again or ask a more specific question."
            return {
                "selected_agent": "clarification_agent",
                "intent": "router_error",
                "confidence": 0.0,
                "reasoning": "The router could not complete this request.",
                "needs_clarification": True,
                "clarification_question": message
            }
