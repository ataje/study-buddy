# Retrieval-augmented generation: a short lecture

## Page 1 — Why retrieval matters

A language model generates text from patterns learned during training. Its knowledge can be incomplete or outdated, and it can produce confident statements that are unsupported. Retrieval-augmented generation (RAG) supplies relevant source passages to the model at answer time. The model uses those passages as context for its answer. RAG does not guarantee correctness: a useful answer still depends on source quality, retrieval quality, and generation quality.

## Page 2 — From a document to relevant passages

A document is split into smaller passages called chunks. Each chunk is converted into an embedding, a numerical vector representing aspects of its meaning. A vector database stores the embeddings alongside their source text and metadata, such as document name and page number. When a user asks a question, the system embeds the query and retrieves similar chunks. Overlapping chunks can preserve context near chunk boundaries. Page metadata helps the reader check the answer against its source.

## Page 3 — Checking the answer

The retrieved passages are supplied to the model with the question. The answer should cite its supporting passages and acknowledge when the context does not contain the answer. A review step can compare a draft with the retrieved evidence, but a second model is not an independent guarantee of truth. Evaluation should include known-answer questions, questions not supported by the source, retrieval checks, and tests of failures such as empty or scanned PDFs. A public demo also needs limits on uploads and model calls.
