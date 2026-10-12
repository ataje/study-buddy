"""Ephemeral, session-isolated vectors; only the embedding model is shared."""
from functools import lru_cache
from threading import RLock
import time
from uuid import uuid4
import chromadb
from chromadb.config import Settings

_collection_lock = RLock()
_model_lock = RLock()
COLLECTION_TTL_SECONDS = 2 * 60 * 60
MAX_ACTIVE_COLLECTIONS = 40


@lru_cache(maxsize=1)
def embedding_model(model_name):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name, device="cpu")


class RetrievalAgent:
    def __init__(self, collection_name=None, model_name="sentence-transformers/all-MiniLM-L6-v2",
                 client=None, model=None):
        self.model_name = model_name
        self.model = model
        self.client = client or chromadb.EphemeralClient(Settings(anonymized_telemetry=False))
        self.collection_name = collection_name or f"studybuddy_{uuid4().hex}"
        self.collection = None
        self.last_sources = []

    def _get_model(self):
        if self.model is None:
            try:
                with _model_lock:
                    self.model = embedding_model(self.model_name)
            except Exception:
                raise RuntimeError("The document search model could not load. Please try again later.") from None
        return self.model

    def chunk_text(self, text, chunk_size=120, overlap=30):
        if chunk_size <= 0 or not 0 <= overlap < chunk_size:
            raise ValueError("Chunk overlap must be smaller than a positive chunk size.")
        words = text.split()
        return [" ".join(words[start:start + chunk_size])
                for start in range(0, len(words), chunk_size - overlap)]

    def index_document(self, text, pages=None, document_name="Lecture"):
        if not text.strip():
            raise ValueError("No readable text was found. Please upload a text-based PDF.")
        pages = pages or [{"page": 1, "text": text}]
        chunks, metadata = [], []
        for page in pages:
            page_chunks = self.chunk_text(page["text"])
            chunks.extend(page_chunks)
            metadata.extend({"page": page["page"], "document": document_name} for _ in page_chunks)
        if not chunks:
            raise ValueError("No readable text was found in this PDF.")
        model = self._get_model()
        with _model_lock:
            vectors = model.encode(chunks, show_progress_bar=False).tolist()
        with _collection_lock:
            self._prune_expired()
            if len(self.client.list_collections()) >= MAX_ACTIVE_COLLECTIONS:
                raise RuntimeError("The demo is busy. Please try again in a few minutes.")
            next_name = f"studybuddy_{uuid4().hex}"
            candidate = self.client.create_collection(next_name, embedding_function=None,
                              metadata={"last_used": time.time()})
            try:
                candidate.add(ids=[f"chunk_{i}" for i in range(len(chunks))],
                              embeddings=vectors, documents=chunks, metadatas=metadata)
            except Exception:
                self.client.delete_collection(next_name)
                raise
            if self.collection is not None:
                try:
                    self.client.delete_collection(self.collection_name)
                except chromadb.errors.NotFoundError:
                    pass
            self.collection_name = next_name
            self.collection = candidate
        self.last_sources = []
        return chunks

    def _prune_expired(self):
        cutoff = time.time() - COLLECTION_TTL_SECONDS
        for collection in self.client.list_collections():
            if not collection.name.startswith("studybuddy_"):
                continue
            if (collection.metadata or {}).get("last_used", 0) < cutoff:
                self.client.delete_collection(collection.name)

    def retrieve(self, query, top_k=3):
        if top_k <= 0:
            raise ValueError("Please request at least one source passage.")
        if self.collection is None:
            raise ValueError("Please prepare a document first.")
        try:
            count = self.collection.count()
        except chromadb.errors.NotFoundError:
            raise ValueError("This study session expired. Please prepare your document again.") from None
        if not count:
            return []
        with _model_lock:
            vector = self._get_model().encode(query).tolist()
        self.collection.modify(metadata={"last_used": time.time()})
        results = self.collection.query(query_embeddings=[vector], n_results=min(top_k, count),
                                        include=["documents", "metadatas"])
        self.last_sources = [dict(meta, text=doc) for doc, meta in
                             zip(results["documents"][0], results["metadatas"][0])]
        return [f"[p. {source['page']}] {source['text']}" for source in self.last_sources]

    def close(self):
        if self.collection is not None:
            try:
                self.client.delete_collection(self.collection_name)
            except chromadb.errors.NotFoundError:
                pass
        self.collection = None
        self.last_sources = []
