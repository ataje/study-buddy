import io
import json
import os
from pathlib import Path
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from document_ingest import extract_pdf, MAX_BYTES
from rag.retrieval_agent import RetrievalAgent
from llm.service import LLMService
from llm.budget import CallBudget, UsageLimitError
from agents.quiz_agent import QuizAgent
from agents.routing_agent import RoutingAgent
from agents.response_review_agent import ResponseReviewAgent


class TestEmbeddings:
    """Fixed test vectors exercise real Chroma storage without a model download."""
    def encode(self, texts, **kwargs):
        def vector(text):
            return [float('banana' in text.lower()), float('planet' in text.lower()), 0.1]
        return np.array([vector(text) for text in texts] if isinstance(texts, list) else vector(texts))


def pdf_bytes(text=None, pages=1, password=None):
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=600, height=800)
        if text is not None:
            font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
            page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
                DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
            stream = DecodedStreamObject()
            stream.set_data(f'BT /F1 12 Tf 72 720 Td ({text}) Tj ET'.encode())
            page[NameObject('/Contents')] = writer._add_object(stream)
    if password:
        writer.encrypt(password)
    output = io.BytesIO(); writer.write(output); output.seek(0)
    return output


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.a = RetrievalAgent(model=TestEmbeddings())
        self.b = RetrievalAgent(model=TestEmbeddings())

    def tearDown(self):
        self.a.close(); self.b.close()

    def test_sessions_do_not_delete_or_expose_each_others_documents(self):
        self.a.index_document('Banana is a fruit.', pages=[{'page': 4, 'text': 'Banana is a fruit.'}], document_name='a.pdf')
        self.b.index_document('Planet is a celestial body.', document_name='b.pdf')
        self.assertIn('Banana', self.a.retrieve('banana', top_k=5)[0])
        self.assertNotIn('Planet', self.a.retrieve('planet')[0])
        self.assertNotIn('Banana', self.b.retrieve('banana')[0])
        self.assertEqual(self.a.last_sources[0]['page'], 4)
        self.assertEqual(self.a.last_sources[0]['document'], 'a.pdf')
        self.b.index_document('Planet orbits a star.')
        self.assertIn('Banana', self.a.retrieve('banana')[0])

    def test_empty_upload_does_not_destroy_previous_document(self):
        self.a.index_document('Banana is a fruit.')
        with self.assertRaises(ValueError):
            self.a.index_document('  ')
        self.assertIn('Banana', self.a.retrieve('banana')[0])

    def test_chunking_parameters_cannot_infinite_loop(self):
        with self.assertRaises(ValueError):
            self.a.chunk_text('hello', chunk_size=30, overlap=30)
        self.assertEqual(self.a.chunk_text(''), [])

    def test_retrieval_before_upload_is_a_useful_error(self):
        with self.assertRaisesRegex(ValueError, 'prepare a document'):
            self.a.retrieve('question')


class PDFTests(unittest.TestCase):
    def test_page_metadata_and_text(self):
        text, pages = extract_pdf(pdf_bytes('A searchable lecture', pages=2))
        self.assertIn('searchable', text)
        self.assertEqual([p['page'] for p in pages], [1, 2])

    def test_blank_encrypted_overlarge_and_too_many_pages(self):
        cases = [(pdf_bytes(), 'No readable'),
                 (pdf_bytes('secret', password='test'), 'password'),
                 (io.BytesIO(b' ' * (MAX_BYTES + 1)), '5 MB'),
                 (pdf_bytes('lecture', pages=41), '40 pages')]
        for file, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                extract_pdf(file)


class BudgetTests(unittest.TestCase):
    def test_public_mode_refuses_ephemeral_counter(self):
        with patch.dict(os.environ, {'APP_ENV': 'public', 'QUOTA_REDIS_URL': '', 'QUOTA_REDIS_TOKEN': ''}):
            budget = CallBudget('a')
            self.assertFalse(budget.ready)
            with self.assertRaises(UsageLimitError):
                budget.reserve()

    def test_atomic_global_daily_limit_under_concurrency(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            'APP_ENV': 'local', 'QUOTA_SQLITE_PATH': str(Path(directory)/'usage.sqlite3'),
            'MAX_DAILY_CALLS': '5', 'MAX_SESSION_CALLS': '30', 'QUOTA_REDIS_URL': '', 'QUOTA_REDIS_TOKEN': ''}):
            def request(i):
                try:
                    CallBudget(str(i)).reserve()
                    return True
                except UsageLimitError:
                    return False
            with ThreadPoolExecutor(max_workers=8) as pool:
                approvals = list(pool.map(request, range(15)))
            self.assertEqual(sum(approvals), 5)
            with self.assertRaises(UsageLimitError):
                CallBudget('new-browser').reserve()

    def test_redis_denial_and_unavailability_fail_closed(self):
        with patch.dict(os.environ, {'APP_ENV':'public', 'QUOTA_REDIS_URL':'https://example.com', 'QUOTA_REDIS_TOKEN':'not-a-real-token'}):
            budget = CallBudget('a')
            with patch('llm.budget.urlopen', return_value=io.StringIO('{"result":0}')):
                with self.assertRaises(UsageLimitError): budget.reserve()
            from urllib.error import URLError
            with patch('llm.budget.urlopen', side_effect=URLError('offline')):
                with self.assertRaises(UsageLimitError): budget.reserve()


class LLMTests(unittest.TestCase):
    def budget(self):
        return SimpleNamespace(ready=True, reserve=lambda: None)

    def test_environment_model_and_endpoint_override_defaults(self):
        with patch.dict(os.environ, {'LIVE_AI_ENABLED':'true', 'LLM_MODEL':'configured-model', 'LLM_BASE_URL':'http://localhost:11434/v1', 'LLM_API_KEY':'', 'OPENAI_API_KEY':''}):
            service = LLMService(budget=self.budget())
            self.assertEqual(service.model_name, 'configured-model')
            self.assertEqual(service.base_url, 'http://localhost:11434/v1')
            self.assertTrue(service.is_configured())

    def test_public_disabled_by_default_and_no_model(self):
        with patch.dict(os.environ, {'LIVE_AI_ENABLED':'false', 'LLM_MODEL':'', 'LLM_API_KEY':''}):
            service = LLMService(budget=self.budget())
            self.assertFalse(service.is_configured())
            with self.assertRaises(RuntimeError): service.generate_text('system','question')

    def test_token_bound_and_provider_error_redaction(self):
        captured=[]
        def create(**kwargs):
            captured.append(kwargs)
            raise RuntimeError('sensitive-provider-detail')
        with patch.dict(os.environ, {'LIVE_AI_ENABLED':'true'}):
            service=LLMService(model_name='test',api_key='test',budget=self.budget())
            service.client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
            with self.assertRaises(RuntimeError) as error: service.generate_text('system','question')
            self.assertNotIn('sensitive',str(error.exception))
            self.assertEqual(captured[0]['max_tokens'],1200)

    def test_invalid_json_types_are_rejected(self):
        service=LLMService(budget=self.budget())
        with patch.object(service,'_create_completion',return_value='[]'):
            with self.assertRaises(RuntimeError): service.generate_json('','')


class AgentTests(unittest.TestCase):
    def test_missing_document_does_not_call_router_model(self):
        fake=SimpleNamespace(is_configured=lambda:True, generate_json=lambda **kw:self.fail('No model call expected'))
        result=RoutingAgent(fake).llm_router_decision('quiz me',False)
        self.assertEqual(result['intent'],'missing_document')

    def test_router_reports_quota_exhaustion_without_diagnostics(self):
        allowance_message="The demo's AI allowance has been reached. Please try the sample preview."
        def reserve():
            raise UsageLimitError(allowance_message) from RuntimeError('sensitive-quota-diagnostic')
        with patch.dict(os.environ, {'LIVE_AI_ENABLED':'true'}):
            service=LLMService(model_name='test',api_key='test',
                               budget=SimpleNamespace(ready=True,reserve=reserve))
            service.client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
                create=lambda **kw:self.fail('Quota exhaustion must prevent the provider request'))))
            result=RoutingAgent(service).llm_router_decision('Explain embeddings',True)
        self.assertEqual(result['selected_agent'],'clarification_agent')
        self.assertTrue(result['needs_clarification'])
        self.assertEqual(result['clarification_question'],allowance_message)
        self.assertNotIn('sensitive',json.dumps(result))

    def test_router_preserves_sanitized_provider_status_messages(self):
        class ProviderFailure(RuntimeError):
            def __init__(self,status):
                super().__init__('sensitive-provider-key-and-account-detail')
                self.status_code=status
        messages={
            429:'The free AI provider is temporarily rate-limited. Wait a minute, then try again.',
            401:'The AI connection needs attention. Check your saved key and model access.',
            403:'The AI connection needs attention. Check your saved key and model access.',
        }
        for status,message in messages.items():
            with self.subTest(status=status),patch.dict(os.environ,{'LIVE_AI_ENABLED':'true'}):
                def create(**kwargs): raise ProviderFailure(status)
                service=LLMService(model_name='test',api_key='test',
                                   budget=SimpleNamespace(ready=True,reserve=lambda:None))
                service.client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
                result=RoutingAgent(service).llm_router_decision('Explain embeddings',True)
                self.assertEqual(result['clarification_question'],message)
                self.assertNotIn('sensitive',json.dumps(result))

    def test_malformed_quizzes_are_rejected_before_display(self):
        from copy import deepcopy
        valid={'title':'Quiz','questions':[{'question':'Which?', 'type':'multiple_choice','options':['A','B'], 'answer':'A','explanation':'A is supported.'}]}
        self.assertEqual(QuizAgent.validate_quiz(valid,1),valid)
        broken=deepcopy(valid); broken['questions'][0]['answer']='C'
        with self.assertRaises(ValueError): QuizAgent.validate_quiz(broken,1)
        with self.assertRaises(ValueError): QuizAgent.validate_quiz(valid,3)

    def test_failed_review_is_not_marked_approved(self):
        fake=SimpleNamespace(is_configured=lambda:True)
        def fail(**kw): raise RuntimeError('offline')
        fake.generate_json=fail
        review=ResponseReviewAgent(fake).review_explanation('question','draft',['source'])
        self.assertFalse(review['approved'])
        self.assertEqual(review['final_response'],'draft')

    def test_multiple_choice_grading_is_deterministic(self):
        fake=SimpleNamespace(generate_json=lambda **kw:self.fail('No model call expected'))
        question={'type':'multiple_choice','answer':'Correct option','explanation':'Because.'}
        agent=QuizAgent(fake)
        self.assertEqual(agent.check_answer(question,'Correct option')['score'],1)
        self.assertEqual(agent.check_answer(question,'Other option')['score'],0)
        self.assertEqual(agent.check_answer(question,'')['score'],0)


if __name__ == '__main__':
    unittest.main()
