import json
import os
import tempfile
import uuid
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import BASE_DIR, CORS_ORIGIN, DATASET_PATH, DEFAULT_LANGUAGE, MAX_FILE_SIZE
from llm_provider import LLMProviderError, generate_answer
from pdf_reader import cleanup_session_files, extract_text_from_pdf, save_uploaded_pdf, validate_pdf_file
from rag import build_grounded_prompt, build_knowledge_base, evaluate_retrieval_sufficiency, retrieve_relevant_passages

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
CORS(
    app,
    resources={r"/api/*": {"origins": [CORS_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"]}},
    supports_credentials=True,
)

with DATASET_PATH.open("r", encoding="utf-8") as source:
    SCHEMES = json.load(source)
with (BASE_DIR / "mahadbt_scheme_names.json").open("r", encoding="utf-8") as source:
    MAHADBT_SCHEMES = json.load(source)

for item in MAHADBT_SCHEMES:
    scheme_id = "mahadbt-" + "".join(
        character if character.isalnum() else "-"
        for character in item["name"].lower()
    ).strip("-")
    SCHEMES.append({
        "id": scheme_id,
        "name": item["name"],
        "category": item["category"],
        "description": f"Scheme listed in the official MahaDBT portal under {item['department']}.",
        "beneficiaries": "Eligibility and beneficiary groups depend on the current official scheme guidelines.",
        "eligibility_summary": "UNVERIFIED in CivicLens AI. Check the current MahaDBT notification before relying on this information.",
        "required_documents": "UNVERIFIED. Check the current MahaDBT application instructions.",
        "verification_status": "UNVERIFIED",
        "source_url": "https://mahadbt.maharashtra.gov.in/",
        "official_title": "MahaDBT Maharashtra",
        "source_passage": f"The official MahaDBT portal lists {item['name']} under {item['department']}."
    })

PDF_SESSIONS = {}


def _load_schemes():
    return SCHEMES


def _build_document_overview(passages):
    text = " ".join(passage.get("text", "") for passage in passages).lower()
    detected = []
    for term, label in (
        ("ews", "EWS / economic-status document"),
        ("economically weaker", "EWS / economic-status document"),
        ("hostel", "hostel or residence document"),
        ("income", "income document"),
        ("caste", "caste or category document"),
        ("disability", "disability document"),
        ("scholarship", "scholarship or education document"),
        ("bonafide", "student or bonafide document"),
    ):
        if term in text and label not in detected:
            detected.append(label)

    uses = [
        "Review the document's issuing authority, validity, date, and named beneficiary.",
        "Use the document only for applications whose official requirements explicitly request it.",
        "Compare the document details with the current scheme notification before submitting it.",
    ]
    if detected:
        uses.insert(0, f"Possible document type detected: {', '.join(detected)}.")

    return {
        "pages_with_text": len(passages),
        "detected_topics": detected,
        "possible_uses": uses,
        "suggested_questions": [
            "What information does this document contain?",
            "What is this document generally used for?",
            "Which page shows the date or validity details?",
            "Can this be relevant to a MahaDBT application?",
        ],
        "notice": "Document classification is a helpful hint, not proof that the document is valid or accepted.",
    }


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "message": "CivicLens AI backend is running."})


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    language = str(payload.get("language", DEFAULT_LANGUAGE)).strip().lower() or DEFAULT_LANGUAGE

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    knowledge = build_knowledge_base(_load_schemes())
    retrieval = retrieve_relevant_passages(question, knowledge, top_n=3, threshold=0.05)
    sufficiency = evaluate_retrieval_sufficiency(retrieval)

    if not retrieval or not sufficiency:
        answer = (
            "I could not find sufficient evidence in the available scheme information to answer that confidently. "
            "Please try a more specific question or review the official source before acting on the information."
        )
        return jsonify({
            "answer": answer,
            "source_passages": [],
            "llm_available": False,
            "language": language,
            "retrieval_sufficient": False,
        })

    try:
        result = generate_answer(question, retrieval, language)
    except LLMProviderError as exc:
        return jsonify({
            "answer": f"AI generation is currently unavailable: {exc}. You can still review the retrieved evidence below.",
            "source_passages": retrieval,
            "llm_available": False,
            "language": language,
            "retrieval_sufficient": True,
        })

    return jsonify({
        "answer": result.get("answer", "No answer available."),
        "source_passages": retrieval,
        "llm_available": result.get("available", False),
        "language": language,
        "retrieval_sufficient": True,
        "citations": result.get("citations", []),
    })


@app.get("/api/schemes")
def list_schemes():
    query = request.args.get("query", "").strip().lower()
    category = request.args.get("category", "").strip()
    schemes = _load_schemes()

    filtered = schemes
    if query:
        filtered = [
            scheme for scheme in filtered
            if query in scheme.get("name", "").lower() or query in scheme.get("description", "").lower()
        ]
    if category:
        filtered = [scheme for scheme in filtered if scheme.get("category") == category]

    return jsonify(filtered)


@app.post("/api/schemes/recommend")
def recommend_schemes():
    payload = request.get_json(silent=True) or {}
    profile = {
        key: str(payload.get(key, "")).strip().lower()
        for key in ("state", "age_group", "education", "social_category", "occupation", "goal")
    }

    if not any(profile.values()):
        return jsonify({"error": "Please provide at least one profile preference."}), 400

    query_parts = [value for value in profile.values() if value]
    knowledge = build_knowledge_base(_load_schemes())
    retrieved = retrieve_relevant_passages(" ".join(query_parts), knowledge, top_n=10, threshold=0.01)
    recommendations = []

    for item in retrieved:
        reasons = []
        category = item.get("category", "").lower()
        content = item.get("content", "").lower()
        goal = profile["goal"]
        if goal and (
            (goal == "education" and "education" in category)
            or (goal == "agriculture" and "agriculture" in category)
            or (goal == "employment" and ("employment" in category or "skill" in category))
            or (goal == "health" and "health" in category)
            or (goal == "housing" and "housing" in category)
            or (goal == "business" and "business" in category)
            or (goal == "social welfare" and "social welfare" in category)
        ):
            reasons.append(f"Matches your {goal} goal")
        for value, label in (
            (profile["education"], "education preference"),
            (profile["social_category"], "social category"),
            (profile["occupation"], "occupation"),
        ):
            if value and value in content:
                reasons.append(f"Related to your {label}")
        if not reasons:
            reasons.append("Related to the preferences you entered")

        scheme = next((candidate for candidate in _load_schemes() if candidate["id"] == item["id"]), None)
        if scheme:
            recommendations.append({
                **scheme,
                "match_reasons": reasons[:2],
                "match_score": round(float(item.get("score", 0)), 3),
            })

    return jsonify({
        "disclaimer": "These are potential matches, not an eligibility decision. Confirm current rules and documents on the official source.",
        "recommendations": recommendations,
    })


@app.get("/api/schemes/<scheme_id>")
def get_scheme(scheme_id):
    for scheme in _load_schemes():
        if scheme.get("id") == scheme_id:
            return jsonify(scheme)
    return jsonify({"error": "Scheme not found."}), 404


@app.post("/api/pdf/upload")
def upload_pdf():
    file_storage = request.files.get("file")
    if not file_storage:
        return jsonify({"error": "No file uploaded."}), 400

    try:
        validate_pdf_file(file_storage)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    session_id = uuid.uuid4().hex
    try:
        saved_path = save_uploaded_pdf(file_storage, session_id)
        extracted = extract_text_from_pdf(saved_path)
    except RuntimeError as exc:
        cleanup_session_files(session_id)
        return jsonify({"error": str(exc)}), 400
    except Exception:
        cleanup_session_files(session_id)
        return jsonify({"error": "Unable to read the uploaded PDF."}), 400

    PDF_SESSIONS[session_id] = {
        "path": saved_path,
        "filename": file_storage.filename,
        "passages": extracted.get("passages", []),
        "full_text": extracted.get("full_text", ""),
        "message": extracted.get("message", ""),
        "page_count": extracted.get("page_count", 0),
    }

    return jsonify({
        "session_id": session_id,
        "filename": file_storage.filename,
        "message": extracted.get("message", "Text extracted successfully."),
        "passages": extracted.get("passages", []),
        "total_pages": extracted.get("page_count", len(extracted.get("passages", []))) or 0,
        "document_overview": _build_document_overview(extracted.get("passages", [])),
    })


@app.post("/api/pdf/ask")
def ask_pdf():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    session_id = str(payload.get("session_id", "")).strip()
    language = str(payload.get("language", DEFAULT_LANGUAGE)).strip().lower() or DEFAULT_LANGUAGE

    if not question:
        return jsonify({"error": "Please enter a question for the uploaded document."}), 400
    if not session_id or session_id not in PDF_SESSIONS:
        return jsonify({"error": "No valid PDF session is available. Please upload a PDF again."}), 400

    session = PDF_SESSIONS[session_id]
    passages = []
    for passage in session.get("passages", []):
        passages.append({
            "title": "Uploaded PDF",
            "content": passage.get("text", ""),
            "metadata": {"page_number": passage.get("page_number")},
        })

    knowledge = build_knowledge_base(pdf_passages=passages)
    retrieval = retrieve_relevant_passages(question, knowledge, top_n=3, threshold=0.01)
    if not retrieval:
        retrieval = knowledge[:3]
    if not retrieval:
        return jsonify({
            "answer": (
                "This PDF has no selectable text, so I cannot answer questions from its contents yet. "
                "It appears to be scanned or image-only. Please upload a text-based PDF or run OCR on the document first."
            ),
            "source_passages": [],
            "llm_available": False,
            "language": language,
            "needs_ocr": True,
        })

    try:
        result = generate_answer(question, retrieval, language)
    except LLMProviderError as exc:
        return jsonify({
            "answer": f"AI generation is currently unavailable: {exc}. Please review the PDF excerpts below.",
            "source_passages": retrieval,
            "llm_available": False,
            "language": language,
        })

    return jsonify({
        "answer": result.get("answer", "No answer available."),
        "source_passages": retrieval,
        "llm_available": result.get("available", False),
        "language": language,
        "citations": result.get("citations", []),
    })


@app.delete("/api/pdf/session")
def clear_pdf_session():
    session_id = request.args.get("session_id", "").strip()
    if session_id in PDF_SESSIONS:
        cleanup_session_files(session_id)
        del PDF_SESSIONS[session_id]
    return jsonify({"status": "ok"})


@app.errorhandler(404)
def handle_not_found(_):
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(500)
def handle_internal_error(error):
    app.logger.exception("Server error: %s", error)
    return jsonify({"error": "A server error occurred. Please try again later."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
