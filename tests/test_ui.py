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

    def test_home_study_navigation_preserves_lesson_and_evidence_without_paid_work(self):
        at=self.app()
        fake=FakeService()
        sources=[{'document':'lecture.pdf','page':2,'text':'Embeddings represent passages as vectors.'}]
        retrieval_calls=[]
        def retrieve(*args,**kw):
            retrieval_calls.append(1)
            return ['[p. 2] Embeddings represent passages as vectors.']
        at.session_state.llm_service=fake
        at.session_state.routing_agent=RoutingAgent(fake)
        at.session_state.explaining_agent=ExplainingAgent(fake)
        at.session_state.response_review_agent=ResponseReviewAgent(fake)
        at.session_state.retrieval_agent=SimpleNamespace(retrieve=retrieve,last_sources=sources)
        at.session_state.document_ready=True
        at.session_state.document_text=sources[0]['text']
        at.session_state.active_document_name='lecture.pdf'
        at.session_state.document_library={'lecture.pdf':{'section_count':1}}
        at.run()
        at.button(key='nav_study').click().run()
        self.assertFalse(at.exception)
        lesson=at.session_state.explanation
        self.assertTrue(lesson)
        self.assertEqual(fake.calls,['text','json'])
        self.assertEqual(len(retrieval_calls),1)
        self.assertEqual(at.session_state.lesson_sources,sources)

        at.button(key='nav_home').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state.page,'home')
        at.button(key='nav_study').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state.page,'explaining')
        self.assertEqual(at.session_state.explanation,lesson)
        self.assertEqual(at.session_state.lesson_sources,sources)
        self.assertEqual(fake.calls,['text','json'])
        self.assertEqual(len(retrieval_calls),1)
        self.assertTrue(any(item.label=='Page 2 · passage 1' for item in at.expander))
        self.assertTrue(any(item.value==sources[0]['text'] for item in at.markdown))

    def test_home_practice_navigation_preserves_quiz_feedback_and_evidence(self):
        at=self.app()
        fake=FakeService()
        question={'type':'multiple_choice','question':'What represents a passage as a vector?',
                  'options':['Embedding','Page number'],'answer':'Embedding','explanation':'Embeddings encode meaning. [p. 2]'}
        short_question={'type':'short_answer','question':'Why retain source page numbers?',
                        'answer':'To verify the answer against the original lecture.'}
        quiz={'title':'Embedding practice','questions':[question,short_question]}
        feedback={'score':1.0,'is_correct':True,'feedback':'Correct.','correct_answer':'Embedding'}
        sources=[{'document':'lecture.pdf','page':2,'text':'Embeddings encode the meaning of passages.'}]
        at.session_state.llm_service=fake
        at.session_state.routing_agent=RoutingAgent(fake)
        at.session_state.document_ready=True
        at.session_state.active_document_name='lecture.pdf'
        at.session_state.document_library={'lecture.pdf':{'section_count':1}}
        at.session_state.quiz_data=quiz
        at.session_state.quiz_query='Test embeddings'
        at.session_state.quiz_feedback={'quiz_feedback_1':feedback}
        at.session_state.revealed_answers={'quiz_answer_1':True}
        at.session_state.quiz_sources=sources
        at.session_state.page='quiz'
        at.run()
        self.assertFalse(at.exception)
        at.radio(key='quiz_question_1').set_value('Embedding').run()
        short_response='Page numbers let me check an answer against the original lecture.'
        at.text_area(key='quiz_short_answer_2').set_value(short_response).run()
        self.assertFalse(at.exception)
        at.button(key='nav_home').click().run()
        at.button(key='nav_practice').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state.page,'quiz')
        self.assertEqual(at.session_state.quiz_data,quiz)
        self.assertEqual(at.session_state.quiz_query,'Test embeddings')
        self.assertEqual(at.session_state.quiz_feedback,{'quiz_feedback_1':feedback})
        self.assertEqual(at.session_state.revealed_answers,{'quiz_answer_1':True})
        self.assertEqual(at.session_state.quiz_sources,sources)
        self.assertEqual(at.radio(key='quiz_question_1').value,'Embedding')
        self.assertEqual(at.text_area(key='quiz_short_answer_2').value,short_response)
        self.assertEqual(at.session_state.quiz_responses,{
            'quiz_question_1':'Embedding','quiz_short_answer_2':short_response})
        self.assertEqual(fake.calls,[])
        self.assertTrue(any(item.value=='Current score: 1.0 / 2' for item in at.caption))
        self.assertEqual(at.button(key='toggle_answer_1').label,'Hide answer')
        self.assertTrue(any(item.label=='Page 2 · passage 1' for item in at.expander))
        self.assertTrue(any(item.value==sources[0]['text'] for item in at.markdown))


if __name__=='__main__': unittest.main()
