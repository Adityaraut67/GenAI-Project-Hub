import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from rag import build_knowledge_base, evaluate_retrieval_sufficiency, retrieve_relevant_passages


def load_schemes():
    with open(Path(__file__).resolve().parents[1] / 'scheme_data.json', 'r', encoding='utf-8') as source:
        return json.load(source)


def test_rag_retrieval_returns_relevant_passages():
    knowledge = build_knowledge_base(load_schemes())
    results = retrieve_relevant_passages('Tell me about scholarships for girls in technical education.', knowledge, top_n=3, threshold=0.05)
    assert results
    assert any(result['title'] for result in results)
    assert evaluate_retrieval_sufficiency(results)


def test_unknown_question_falls_back_gracefully():
    knowledge = build_knowledge_base(load_schemes())
    results = retrieve_relevant_passages('xyz impossible question about a far away planet', knowledge, top_n=3, threshold=0.3)
    assert results == []
