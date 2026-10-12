import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from agents.routing_agent import RoutingAgent
from agents.query_enhancer_agent import QueryEnhancerAgent
from agents.explaining_agent import ExplainingAgent
from agents.response_review_agent import ResponseReviewAgent


class FakeService:
    def __init__(self): self.calls=[]
    def is_configured(self): return True
    def generate_json(self,system_prompt,user_prompt,**kw):
        self.calls.append('json')
        if 'deciding/routing' in system_prompt:
            return {'selected_agent':'explaining_agent','intent':'explain'}
        if 'query enhancement' in system_prompt:
            return {'enhanced_query':'Explain embeddings','retrieval_query':'embeddings','needs_clarification':False}
        return {'final_response':'An embedding represents text as a vector. [p. 2]','approved':True,'notes':'Reviewed.'}
    def generate_text(self,**kw):
        self.calls.append('text')
        return 'An embedding represents text as a vector. [p. 2]'


class UITests(unittest.TestCase):
    def app(self):
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        self.assertFalse(at.exception)
        return at

    def test_sample_preview_needs_no_provider_and_grades_quiz(self):
        with patch.dict(os.environ,{'LIVE_AI_ENABLED':'false'}):
            at=self.app()
            self.assertTrue(at.button(key='btn_study').disabled)
            at.button(key='try_sample').click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.title[0].value,'A lecture, made interactive')
            self.assertIn('prewritten',at.info[0].value)
            for radio in at.radio: radio.set_value(radio.options[0])
            at.button[-1].click().run()
            self.assertFalse(at.exception)
            self.assertIn('3 / 3',at.success[0].value)
            at.button(key='sample_back').click().run()
            self.assertFalse(at.exception)

    def test_smart_request_does_not_repeat_paid_work_on_rerun(self):
        at=self.app()
        fake=FakeService()
        at.session_state.llm_service=fake
        at.session_state.routing_agent=RoutingAgent(fake)
        at.session_state.query_enhancer_agent=QueryEnhancerAgent(fake)
        at.session_state.explaining_agent=ExplainingAgent(fake)
        at.session_state.response_review_agent=ResponseReviewAgent(fake)
        at.session_state.document_ready=True
        at.session_state.document_text='Embeddings represent passages as vectors.'
        at.session_state.retrieval_agent=SimpleNamespace(retrieve=lambda *args,**kw:['[p. 2] Embeddings represent passages as vectors.'],last_sources=[])
        at.session_state.route='other'
        at.run()
        at.text_input[0].set_value('Explain embeddings')
        at.button(key='submit_other').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(fake.calls),4)
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(len(fake.calls),4)
        self.assertEqual(at.session_state.other_payload['answer'],'An embedding represents text as a vector. [p. 2]')

    def test_failed_lesson_is_not_automatically_retried(self):
        at=self.app()
        count=[]
        def fail(*args,**kw):
            count.append(1)
            raise RuntimeError('Provider unavailable')
        at.session_state.page='explaining'
        at.session_state.retrieval_agent=SimpleNamespace(retrieve=fail,last_sources=[])
        at.run(); at.run()
        self.assertFalse(at.exception)
        self.assertEqual(len(count),1)


if __name__=='__main__': unittest.main()
