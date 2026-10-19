
import json
import os
import random
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )

client = genai.Client(api_key=API_KEY)


def generate_text(prompt, json_mode=False, max_retries=3):
    config = (
        {"response_mime_type": "application/json"}
        if json_mode
        else None
    )

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config,
            )

            if not response.text:
                raise RuntimeError("Gemini returned an empty response.")

            return response.text

        except errors.APIError as error:
            status_code = getattr(error, "code", None)

            if status_code not in (429, 500, 502, 503, 504):
                raise

            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"Gemini is temporarily unavailable after "
                    f"{max_retries} attempts. Please try again later. "
                    f"Details: {error}"
                ) from error

            time.sleep(
                min(2 ** attempt, 8) + random.uniform(0, 0.5)
            )


def generate_summary(document_text):
    text = document_text[:18000]

    prompt = f"""
Summarize the following study material clearly.

Include:
1. Main concepts
2. Important definitions
3. Key points
4. Examples mentioned in the material
5. A short revision summary

Use headings and bullet points. Do not invent information.

STUDY MATERIAL:
{text}
"""
    return generate_text(prompt)


def answer_question(question, retrieved_chunks):
    context_parts = []

    for chunk in retrieved_chunks:
        page = chunk.get("page", "Unknown")
        text = chunk.get("text", "")
        context_parts.append(f"Page {page}:\n{text}")

    context = "\n\n".join(context_parts)

    prompt = f"""
Answer the student's question using the supplied PDF excerpts.

If the excerpts do not contain enough information, clearly say so.
Do not invent facts. Mention relevant page numbers when available.

PDF EXCERPTS:
{context}

QUESTION:
{question}
"""
    return generate_text(prompt)


def generate_quiz(document_text, number_of_questions=5):
    text = document_text[:14000]

    prompt = f"""
Create exactly {number_of_questions} multiple-choice questions
using only the supplied study material.

Return valid JSON in this structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "topic": "Specific concept being tested",
      "options": [
        "First option",
        "Second option",
        "Third option",
        "Fourth option"
      ],
      "answer": "Exact text of the correct option",
      "explanation": "Why this answer is correct"
    }}
  ]
}}

Rules:
- Every question must have exactly four distinct options.
- The correct answer must exactly match one option.
- Assign a short, meaningful topic to every question.
- Use specific concepts from the material.
- Avoid duplicate questions.
- Do not invent facts outside the material.

STUDY MATERIAL:
{text}
"""

    result = generate_text(prompt, json_mode=True)

    try:
        quiz = json.loads(result)
        questions = quiz["questions"]

        if len(questions) != number_of_questions:
            raise ValueError("Incorrect number of questions.")

        for item in questions:
            required = {
                "question", "topic", "options",
                "answer", "explanation"
            }

            if not required.issubset(item):
                raise ValueError("A question is missing required fields.")

            if not isinstance(item["topic"], str) or not item["topic"].strip():
                raise ValueError("A question has an invalid topic.")

            if (
                not isinstance(item["options"], list)
                or len(item["options"]) != 4
                or not all(isinstance(option, str) for option in item["options"])
            ):
                raise ValueError("Each question needs four text options.")

            if len(set(item["options"])) != 4:
                raise ValueError("Options must be distinct.")

            if item["answer"] not in item["options"]:
                raise ValueError("Correct answer is not a valid option.")

        return questions

    except (ValueError, KeyError, TypeError) as error:
        raise RuntimeError(
            f"Could not validate the generated quiz: {error}"
        ) from error
