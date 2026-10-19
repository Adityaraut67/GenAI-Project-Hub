
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_chunks(pages, chunk_size=180, overlap=40):
    chunks = []

    for page in pages:
        words = page["text"].split()
        start = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))

            chunk_text = " ".join(words[start:end])

            if chunk_text.strip():
                chunks.append({
                    "page": page["page"],
                    "text": chunk_text
                })

            if end == len(words):
                break

            start = end - overlap

    return chunks


def build_index(chunks):
    if not chunks:
        raise ValueError("No readable text found in the PDF.")

    texts = [chunk["text"] for chunk in chunks]

    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    return index


def search_chunks(question, chunks, index, top_k=4):
    if not chunks:
        return []

    query_vector = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    count = min(top_k, len(chunks))
    scores, indices = index.search(query_vector, count)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append({
                **chunks[int(idx)],
                "similarity": float(score)
            })

    return results
