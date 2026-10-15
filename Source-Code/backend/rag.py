import re
from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    cleaned = re.sub(r"\s+", " ", str(text))
    return cleaned.strip()


def build_knowledge_base(schemes: List[Dict[str, Any]] | None = None, pdf_passages: List[Dict[str, Any]] | None = None):
    records: List[Dict[str, Any]] = []

    for scheme in schemes or []:
        parts = [
            scheme.get("name", ""),
            scheme.get("category", ""),
            scheme.get("description", ""),
            scheme.get("beneficiaries", ""),
            scheme.get("eligibility_summary", ""),
            scheme.get("required_documents", ""),
            scheme.get("source_url", ""),
            scheme.get("official_title", ""),
            scheme.get("source_passage", ""),
            scheme.get("verification_status", ""),
        ]
        records.append({
            "id": scheme.get("id", "scheme"),
            "title": scheme.get("name", "Scheme"),
            "category": scheme.get("category", "General"),
            "source_type": "scheme",
            "content": " ".join(part for part in parts if part),
            "url": scheme.get("source_url"),
            "metadata": {
                "verification_status": scheme.get("verification_status", "UNVERIFIED"),
            },
        })

    for idx, passage in enumerate(pdf_passages or []):
        passage_text = passage.get("text") or passage.get("content", "")
        if not passage_text:
            continue
        records.append({
            "id": f"pdf_{idx}",
            "title": passage.get("title", "Uploaded PDF"),
            "category": "Uploaded PDF",
            "source_type": "pdf",
            "content": passage_text,
            "url": None,
            "metadata": {
                "page_number": passage.get("page_number")
                if passage.get("page_number") is not None
                else passage.get("metadata", {}).get("page_number"),
            },
        })

    return records


def retrieve_relevant_passages(question: str, knowledge_base, top_n: int = 3, threshold: float = 0.05):
    if not question or not knowledge_base:
        return []

    normalized_question = normalize_text(question)
    if not normalized_question:
        return []

    corpus = [normalize_text(item.get("content", "")) for item in knowledge_base]
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([normalized_question, *corpus])
    cosine_matrix = cosine_similarity(vectors[0:1], vectors[1:])

    ranked = []
    for index, score in enumerate(cosine_matrix[0]):
        if score >= threshold:
            ranked.append({
                "index": index,
                "score": float(score),
                **knowledge_base[index],
            })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_n]


def build_grounded_prompt(question: str, passages: List[Dict[str, Any]], language: str = "en") -> str:
    language_label = {
        "en": "English",
        "hi": "Hindi",
        "mr": "Marathi",
    }.get(language, "English")

    evidence_lines = []
    for idx, passage in enumerate(passages, start=1):
        source = passage.get("title") or passage.get("name") or "Source"
        metadata = passage.get("metadata", {})
        page_number = metadata.get("page_number")
        url = passage.get("url")
        location = f" (page {page_number})" if page_number is not None else ""
        citation = f"Source {idx}: {source}{location}"
        if url:
            citation += f" | URL: {url}"
        evidence_lines.append(f"{citation}\n{passage.get('content', '')}\n")

    evidence_block = "\n\n".join(evidence_lines) if evidence_lines else "No verified evidence was provided."

    return (
        f"You are CivicLens AI, an informational assistant for public government information. "
        f"Answer in {language_label}. Use the retrieved evidence as the primary source. "
        "Never invent eligibility, documents, deadlines, benefits, or official links. "
        "If evidence is limited or missing, clearly explain that limitation. "
        "Do not claim to submit applications, approve applications, or make legal decisions. "
        "Important: distinguish verified facts from unverified information and recommend checking the official source before important decisions.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"RETRIEVED EVIDENCE:\n{evidence_block}\n\n"
        "Create a short answer followed by brief explanation, relevant requirements if supported by evidence, important limitations, sources, and suggested next steps."
    )


def evaluate_retrieval_sufficiency(passages: List[Dict[str, Any]], threshold: float = 0.05) -> bool:
    if not passages:
        return False
    return any(float(item.get("score", 0)) >= threshold for item in passages)


def build_local_document_answer(question: str, passages: List[Dict[str, Any]]) -> str:
    """Return a useful evidence-only answer when no external LLM is configured."""
    if not passages:
        return (
            "No readable evidence was found in the uploaded document. "
            "This version supports text-based PDFs and does not yet include OCR."
        )

    all_text = " ".join(normalize_text(item.get("content", "")) for item in passages).lower()
    question_lower = question.lower()
    interpretation = []
    if "hostel" in all_text:
        interpretation.append(
            "This appears to be a hostel-related certificate or proof of hostel residence. "
            "It may be useful when an official scholarship, fee-support, or hostel-benefit application "
            "asks for proof that the student is staying in a hostel."
        )
    if "economically weaker" in all_text or "ews" in all_text:
        interpretation.append(
            "The document also contains EWS/economic-status wording. It may be relevant to "
            "EWS-based applications when the current rules request this certificate."
        )
    if "income" in all_text:
        interpretation.append(
            "Income-related wording is present, so an application may use it as income evidence "
            "only where the official authority accepts this certificate."
        )
    if "valid" in all_text or "validity" in all_text:
        interpretation.append(
            "The OCR text appears to contain validity or date information. Check the original page "
            "carefully because OCR can misread dates."
        )
    if not interpretation:
        interpretation.append(
            "The extracted text does not provide enough reliable detail to identify a specific official use."
        )

    question_words = {
        word.lower()
        for word in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9-]{2,}", question)
    }
    selected = []
    for passage in passages:
        content = normalize_text(passage.get("content", ""))
        content_words = set(re.findall(r"[a-zA-Z0-9][a-zA-Z0-9-]{2,}", content.lower()))
        overlap = len(question_words & content_words)
        if overlap or len(selected) < 2:
            selected.append((overlap, passage))

    selected.sort(key=lambda item: item[0], reverse=True)
    excerpts = []
    for _, passage in selected[:3]:
        page = passage.get("metadata", {}).get("page_number", "?")
        excerpts.append(f"Page {page}: {normalize_text(passage.get('content', ''))[:700]}")

    is_pdf = any(item.get("source_type") == "pdf" for item in passages)
    evidence_label = "OCR/text extracted from your PDF" if is_pdf else "retrieved evidence"
    answer_intro = (
        f"AI generation is not configured, so this evidence-only answer is based on {evidence_label}.\n\n"
        "Answer based on the evidence:\n"
    )
    if any(word in question_lower for word in ("use", "purpose", "what is this", "scheme", "mahadbt")):
        answer_intro += "\n".join(f"- {item}" for item in interpretation)
    else:
        answer_intro += (
            f"I found document evidence relevant to your question about \"{question}\". "
            "The likely interpretation is:\n"
            + "\n".join(f"- {item}" for item in interpretation)
        )

    return (
        answer_intro
        + "\n\nSupporting pages:\n\n"
        + "\n\n".join(excerpts)
        + (
            "\n\nImportant: OCR can misread names, numbers, dates, and seals. Confirm the original "
            "certificate and the current official scheme requirements before submitting it."
            if is_pdf
            else "\n\nConfirm important details with the official source before acting on this answer."
        )
    )
