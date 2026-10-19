import hashlib
import json

import streamlit as st

import pandas as pd

import plotly.express as px



from utils.pdf_loader import extract_pdf_pages

from utils.embeddings import create_chunks, build_index, search_chunks



from utils.ai_engine import (

    generate_summary,

    answer_question,

    generate_quiz,

)



from utils.database import (

    init_db,

    save_attempt,

    get_attempts,

    get_weak_topics,

    get_weak_questions,

    clear_history,

    init_document_table,

    save_document,

    get_documents,

    get_document,

    delete_document,

)





# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(

    page_title="SmartNotes AI",

    page_icon="📚",

    layout="wide",

    initial_sidebar_state="expanded",

)

init_db()

init_document_table()

# ---------------- CUSTOM UI ----------------

st.markdown(

    """

    <style>

    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }

    [data-testid="stSidebar"] { border-right: 1px solid #e5e7eb; }

    .hero {

        padding: 1.5rem; border-radius: 18px;

        background: linear-gradient(120deg, #eef2ff, #f5f3ff);

        border: 1px solid #e0e7ff; margin-bottom: 1.3rem;

    }

    .hero h1 { color: #312e81; margin-bottom: .4rem; }

    .hero p { color: #4b5563; margin-bottom: 0; }

    div[data-testid="stMetric"] {

        background: #fff; border: 1px solid #e5e7eb;

        padding: 16px; border-radius: 14px;

    }

    div.stButton > button { border-radius: 10px; font-weight: 500; }

    </style>

    """,

    unsafe_allow_html=True,

)



# ---------------- SESSION STATE ----------------

defaults = {

    "study_data": None,

    "file_hash": None,

    "summary": None,

    "quiz": None,

    "quiz_result": None,

    "chat_history": [],

    "document_name": None,

    "page_nav": "🏠 Dashboard",

}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value





def navigate_to(target):

    st.session_state["page_nav"] = target





def render_hero(title, subtitle):

    st.markdown(

        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',

        unsafe_allow_html=True,

    )





def require_document():

    if st.session_state.get("study_data") is None:

        st.warning("Upload a PDF using the sidebar before using this feature.")

        return False

    return True





# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.markdown("## 📚 SmartNotes AI")

    st.caption("Your personal study companion")

    st.divider()



    page = st.radio(

        "NAVIGATION",

        [

            "🏠 Dashboard",

            "📄 My Documents",

            "📝 AI Notes",

            "💬 Ask Your PDF",

            "🧠 Practice Quiz",

            "📈 Study Progress",

        ],

        key="page_nav",

        label_visibility="visible",

    )



    st.divider()



# ---------------- MULTI-DOCUMENT LIBRARY ----------------

st.markdown("### 📚 Upload Study Material")



uploaded_files = st.file_uploader(

    "Choose one or more PDFs",

    type=["pdf"],

    accept_multiple_files=True,

    help="Upload multiple text-based PDFs for your study library.",

    key="multi_pdf_uploader",

)



if "document_library" not in st.session_state:

    st.session_state["document_library"] = {}



if "active_document_hash" not in st.session_state:

    st.session_state["active_document_hash"] = None


if "ignored_upload_hashes" not in st.session_state:
    st.session_state["ignored_upload_hashes"] = set()


# Restore documents saved in SQLite after a new session or server restart.
# Stored text is currently saved as a single string, so page boundaries are
# reconstructed approximately from paragraph breaks.
for saved_document in get_documents():
    saved_hash = saved_document["file_hash"]

    if saved_hash in st.session_state["document_library"]:
        continue

    stored_document = get_document(saved_hash)
    if not stored_document:
        continue

    saved_text = stored_document.get("document_text") or ""
    # Prefer the exact page structure saved in SQLite. Fall back to paragraph
    # reconstruction for older database rows created before this update.
    restored_pages = stored_document.get("pages") or []
    if not restored_pages:
        paragraphs = [part.strip() for part in saved_text.split("\\n\\n") if part.strip()]
        restored_pages = [
            {"page": page_number, "text": paragraph}
            for page_number, paragraph in enumerate(paragraphs, start=1)
        ]

    restored_chunks = create_chunks(restored_pages)
    restored_index = build_index(restored_chunks)

    restored_data = {
        "pages": restored_pages,
        "chunks": restored_chunks,
        "index": restored_index,
        "document_text": saved_text,
        "page_count": stored_document.get("page_count", len(restored_pages)),
        "chunk_count": len(restored_chunks),
    }

    st.session_state["document_library"][saved_hash] = {
        "document_name": stored_document["document_name"],
        "study_data": restored_data,
    }

if (
    st.session_state["active_document_hash"] is None
    and st.session_state["document_library"]
):
    st.session_state["active_document_hash"] = next(
        iter(st.session_state["document_library"])
    )



# Process uploaded PDFs and add them to the session library.

if uploaded_files:

    for uploaded_file in uploaded_files:

        pdf_bytes = uploaded_file.getvalue()

        file_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Prevent a just-removed file from being re-added while it remains
        # selected in Streamlit's uploader widget.
        if file_hash in st.session_state["ignored_upload_hashes"]:
            continue

        if file_hash in st.session_state["document_library"]:

            continue



        try:

            with st.spinner(f"Indexing {uploaded_file.name}..."):

                pages = extract_pdf_pages(pdf_bytes)



                if not pages:

                    st.warning(

                        f"No readable text found in {uploaded_file.name}. "

                        "Try a text-based PDF."

                    )

                    continue



                chunks = create_chunks(pages)

                index = build_index(chunks)



                document_data = {

                    "pages": pages,

                    "chunks": chunks,

                    "index": index,

                    "document_text": "\n\n".join(

                        p["text"] for p in pages

                    ),

                    "page_count": len(pages),

                    "chunk_count": len(chunks),

                }



                # Persist extracted text and metadata in SQLite.
                save_document(
                    file_hash=file_hash,
                    document_name=uploaded_file.name,
                    document_text=document_data["document_text"],
                    page_count=document_data["page_count"],
                    pages=document_data["pages"],
                )

                st.session_state["document_library"][file_hash] = {
                    "document_name": uploaded_file.name,
                    "study_data": document_data,
                }



                if st.session_state["active_document_hash"] is None:

                    st.session_state["active_document_hash"] = file_hash



        except Exception as error:

            st.error(

                f"Could not process {uploaded_file.name}: {error}"

            )



library = st.session_state["document_library"]



if library:

    st.success(f"{len(library)} PDF(s) in your current study library.")



    # Let the user choose the active PDF.

    document_hashes = list(library.keys())

    document_labels = {

        key: library[key]["document_name"]

        for key in document_hashes

    }



    current_hash = st.session_state["active_document_hash"]

    if current_hash not in library:

        current_hash = document_hashes[0]



    selected_hash = st.selectbox(

        "Select the document you want to study",

        options=document_hashes,

        format_func=lambda key: document_labels[key],

        index=document_hashes.index(current_hash),

        key="selected_library_document",

    )



    if selected_hash != st.session_state["active_document_hash"]:

        st.session_state["active_document_hash"] = selected_hash



        # Reset document-specific generated content when switching PDFs.

        st.session_state["summary"] = None

        st.session_state["quiz"] = None

        st.session_state["quiz_result"] = None

        st.session_state["chat_history"] = []



    active_entry = library[st.session_state["active_document_hash"]]



    st.session_state["document_name"] = active_entry["document_name"]

    st.session_state["study_data"] = active_entry["study_data"]

    st.session_state["file_hash"] = st.session_state["active_document_hash"]



    st.caption("Powered by Gemini + RAG")



else:

    st.session_state["study_data"] = None

    st.session_state["document_name"] = None

    st.session_state["file_hash"] = None

    st.caption("Upload a PDF to get started.")



data = st.session_state.get("study_data")

attempts = get_attempts()

total_quizzes = len(attempts)

average_score = (

    sum(item["percentage"] for item in attempts) / total_quizzes

    if total_quizzes else 0

)



# ---------------- DASHBOARD ----------------



if page == "🏠 Dashboard":

    render_hero(

        "Welcome to SmartNotes AI 👋",

        "Your personal AI-powered workspace for smarter learning and revision.",

    )



    # ---------------- OVERVIEW METRICS ----------------

    st.subheader("Your Learning Overview")



    col1, col2, col3 = st.columns(3)



    with col1:

        st.metric(

            "📄 Current Document",

            "Ready" if data else "Not uploaded",

        )



    with col2:

        st.metric(

            "🧠 Quizzes Completed",

            total_quizzes,

        )



    with col3:

        st.metric(

            "🎯 Average Quiz Score",

            f"{average_score:.1f}%",

        )



    st.divider()



    # ---------------- QUICK ACTIONS ----------------

    st.subheader("Your Study Workspace")

    st.caption("Choose a tool to continue your learning.")



    c1, c2 = st.columns(2)



    with c1:

        with st.container(border=True):

            st.markdown("### 📝 AI Notes")

            st.write(

                "Turn lengthy study material into clear summaries "

                "and structured revision notes."

            )

            st.button(

                "Open AI Notes →",

                key="dashboard_ai_notes",

                use_container_width=True,

                on_click=navigate_to,

                args=("📝 AI Notes",),

            )



        with st.container(border=True):

            st.markdown("### 🧠 Practice Quiz")

            st.write(

                "Test your understanding with MCQs, correct answers, "

                "and explanations."

            )

            st.button(

                "Start a Quiz →",

                key="dashboard_practice_quiz",

                use_container_width=True,

                on_click=navigate_to,

                args=("🧠 Practice Quiz",),

            )



    with c2:

        with st.container(border=True):

            st.markdown("### 💬 Ask Your PDF")

            st.write(

                "Ask questions about your uploaded material "

                "and explore relevant passages."

            )

            st.button(

                "Ask a Question →",

                key="dashboard_ask_pdf",

                use_container_width=True,

                on_click=navigate_to,

                args=("💬 Ask Your PDF",),

            )



        with st.container(border=True):

            st.markdown("### 📈 Study Progress")

            st.write(

                "Review your quiz history, track scores, "

                "and identify topics that need revision."

            )

            st.button(

                "View Progress →",

                key="dashboard_study_progress",

                use_container_width=True,

                on_click=navigate_to,

                args=("📈 Study Progress",),

            )



    st.divider()



    # ---------------- CURRENT DOCUMENT ----------------

    st.subheader("📚 Current Study Material")



    if data:

        with st.container(border=True):

            st.markdown(

                f"### 📄 {st.session_state['document_name']}"

            )



            m1, m2, m3 = st.columns(3)



            m1.metric("Readable Pages", data["page_count"])

            m2.metric("Searchable Chunks", data["chunk_count"])

            m3.metric(

                "Extracted Characters",

                f"{len(data['document_text']):,}",

            )



            st.success(

                "Your study material is ready for summaries, "

                "questions, and quiz generation."

            )



            with st.expander("Preview extracted text"):

                st.text(data["document_text"][:3000])



            st.download_button(

                "⬇️ Download Extracted Text",

                data=data["document_text"],

                file_name="extracted_study_material.txt",

                mime="text/plain",

                use_container_width=True,

                key="dashboard_download_text",

            )



    else:

        with st.container(border=True):

            st.markdown("### Get started with your first document")

            st.write(

                "Upload a PDF to generate notes, ask questions, "

                "and create practice quizzes."

            )

            st.button(

                "Open My Documents →",

                key="dashboard_open_documents",

                use_container_width=True,

                on_click=navigate_to,

                args=("📄 My Documents",),

            )



    # ---------------- RECENT QUIZ ACTIVITY ----------------

    st.divider()

    st.subheader("🕒 Recent Quiz Activity")



    recent_attempts = get_attempts()



    if recent_attempts:

        for attempt in recent_attempts[:3]:

            score = attempt.get("score", 0)

            total = attempt.get("total_questions", 0)

            percentage = attempt.get("percentage", 0)



            with st.container(border=True):

                activity_col1, activity_col2 = st.columns(

                    [3, 1]

                )



                with activity_col1:

                    st.markdown(

                        f"**{attempt.get('document_name', 'Study Document')}**"

                    )

                    st.caption(

                        f"{score}/{total} correct answers"

                    )



                with activity_col2:

                    st.metric(

                        "Score",

                        f"{percentage:.1f}%",

                    )

    else:

        st.info(

            "No quiz activity yet. Complete your first practice quiz "

            "to see your recent activity here."

        )









# ---------------- DOCUMENTS ----------------
elif page == "📄 My Documents":
    render_hero(
        "My Documents",
        "Search, select, review, and remove saved study materials.",
    )

    search_term = st.text_input(
        "Search saved documents by filename",
        key="document_search_term",
        placeholder="Enter a filename...",
    )

    saved_documents = get_documents(search_term)
    if not saved_documents:
        st.info("No matching saved documents. Upload a PDF from the sidebar.")
    else:
        st.caption(f"{len(saved_documents)} saved document(s) found.")

        for saved_document in saved_documents:
            doc_hash = saved_document["file_hash"]
            doc_name = saved_document["document_name"]

            with st.container(border=True):
                row_left, row_right = st.columns([4, 1])
                with row_left:
                    st.markdown(f"**📄 {doc_name}**")
                    st.caption(
                        f"Pages: {saved_document['page_count']} · "
                        f"Saved: {saved_document['created_at']}"
                    )
                    if doc_hash == st.session_state.get("active_document_hash"):
                        st.success("Currently selected")
                    elif st.button(
                        "Study this PDF",
                        key=f"select_document_{doc_hash}",
                        use_container_width=True,
                    ):
                        st.session_state["active_document_hash"] = doc_hash
                        st.session_state["summary"] = None
                        st.session_state["quiz"] = None
                        st.session_state["quiz_result"] = None
                        st.session_state["chat_history"] = []
                        st.rerun()

                with row_right:
                    confirm_delete = st.checkbox(
                        "Confirm",
                        key=f"confirm_delete_{doc_hash}",
                    )
                    if st.button(
                        "Remove",
                        key=f"delete_document_{doc_hash}",
                        disabled=not confirm_delete,
                        use_container_width=True,
                    ):
                        delete_document(doc_hash)
                        st.session_state["ignored_upload_hashes"].add(doc_hash)
                        st.session_state["document_library"].pop(doc_hash, None)

                        if st.session_state.get("active_document_hash") == doc_hash:
                            st.session_state["active_document_hash"] = (
                                next(iter(st.session_state["document_library"]), None)
                            )
                            st.session_state["study_data"] = None
                            st.session_state["document_name"] = None
                            st.session_state["file_hash"] = None
                            st.session_state["summary"] = None
                            st.session_state["quiz"] = None
                            st.session_state["quiz_result"] = None
                            st.session_state["chat_history"] = []

                        st.success(f"Removed {doc_name}.")
                        st.rerun()

    data = st.session_state.get("study_data")
    if data:
        st.divider()
        st.subheader("Selected Study Material")
        st.markdown(f"### 📄 {st.session_state['document_name']}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Readable pages", data["page_count"])
        c2.metric("Text chunks", data["chunk_count"])
        c3.metric("Extracted characters", f"{len(data['document_text']):,}")

        with st.expander("Preview extracted text"):
            st.text(data["document_text"][:10000])

        st.download_button(
            "Download extracted text",
            data=data["document_text"],
            file_name="extracted_study_material.txt",
            mime="text/plain",
            key="documents_download_text",
        )
    else:
        st.info("Choose a saved document or upload a PDF from the sidebar.")

# ---------------- AI NOTES ----------------

elif page == "📝 AI Notes":

    render_hero("AI Notes Generator", "Create clear revision notes from your uploaded PDF.")

    if require_document():

        if st.button("✨ Generate Revision Notes", type="primary"):

            try:

                with st.spinner("Gemini is generating your notes..."):

                    st.session_state["summary"] = generate_summary(data["document_text"])

            except Exception as error:

                st.error(str(error))



        if st.session_state.get("summary"):

            st.markdown("### Your Revision Notes")

            st.markdown(st.session_state["summary"])

            st.download_button(

                "⬇️ Download Notes",

                data=st.session_state["summary"],

                file_name="smartnotes_revision_notes.md",

                mime="text/markdown",

            )





# ---------------- ASK YOUR PDF ----------------

elif page == "💬 Ask Your PDF":

    render_hero("Chat with Your PDF", "Answers are generated using passages retrieved from your material.")

    if require_document():

        for message in st.session_state["chat_history"]:

            with st.chat_message(message["role"]):

                st.markdown(message["content"])

                if message.get("sources"):

                    with st.expander("Supporting passages"):

                        for source in message["sources"]:

                            st.markdown(f"**Page {source['page']}**")

                            st.write(source["text"])



        question = st.chat_input("Ask something about your study material...")

        if question:

            st.session_state["chat_history"].append(

                {"role": "user", "content": question}

            )

            try:

                with st.spinner("Searching your notes..."):

                    passages = search_chunks(

                        question, data["chunks"], data["index"], top_k=4

                    )

                    answer = answer_question(question, passages)

                st.session_state["chat_history"].append({

                    "role": "assistant",

                    "content": answer,

                    "sources": passages,

                })

                st.rerun()

            except Exception as error:

                st.error(str(error))





# ---------------- PRACTICE QUIZ ----------------

elif page == "🧠 Practice Quiz":

    render_hero("Practice Quiz", "Test your understanding with questions generated from your notes.")

    if require_document():

        question_count = st.selectbox("Number of questions", [3, 5, 10], index=1)



        if st.button("✨ Generate Quiz", type="primary"):

            try:

                with st.spinner("Gemini is preparing your quiz..."):

                    st.session_state["quiz"] = generate_quiz(

                        data["document_text"], question_count

                    )

                    st.session_state["quiz_result"] = None

            except Exception as error:

                st.error(str(error))



        quiz = st.session_state.get("quiz")

        if quiz:

            with st.form("smartnotes_quiz"):

                answers = []

                for i, item in enumerate(quiz):

                    st.markdown(f"**Question {i + 1}. {item['question']}**")

                    answer = st.radio(

                        "Select an answer",

                        item["options"],

                        index=None,

                        key=f"quiz_{st.session_state['file_hash']}_{i}",

                        label_visibility="collapsed",

                    )

                    answers.append(answer)

                submitted = st.form_submit_button("Submit Quiz", type="primary")



            if submitted:

                unanswered = sum(answer is None for answer in answers)

                if unanswered:

                    st.warning(

                        f"Answer all questions before submitting. "

                        f"{unanswered} remain unanswered."

                    )

                else:

                    score = sum(

                        answer == item["answer"]

                        for answer, item in zip(answers, quiz)

                    )

                    wrong = [

                        {

                            "question": item["question"],

                            "topic": item.get("topic", "Uncategorized"),

                            "selected": answer,

                            "correct": item["answer"],

                            "explanation": item["explanation"],

                        }

                        for answer, item in zip(answers, quiz)

                        if answer != item["answer"]

                    ]

                    save_attempt(

                        st.session_state["document_name"],

                        len(quiz),

                        score,

                        wrong,

                    )

                    st.session_state["quiz_result"] = {

                        "score": score,

                        "answers": answers,

                        "wrong": wrong,

                    }

                    st.rerun()



            result = st.session_state.get("quiz_result")

            if result:

                st.divider()

                st.subheader("Your Results")

                score, total = result["score"], len(quiz)

                c1, c2 = st.columns(2)

                c1.metric("Score", f"{score}/{total}")

                c2.metric("Percentage", f"{score / total * 100:.1f}%")

                st.progress(score / total)



                if score == total:

                    st.success("Excellent! You answered every question correctly.")

                else:

                    st.info("Review the explanations below and revisit difficult topics.")



                for i, item in enumerate(quiz):

                    correct = result["answers"][i] == item["answer"]

                    with st.expander(

                        f"Question {i + 1} — {'Correct ✅' if correct else 'Review ❗'}"

                    ):

                        st.write(f"Topic: {item.get('topic', 'Uncategorized')}")

                        st.write(f"Your answer: {result['answers'][i]}")

                        st.write(f"Correct answer: {item['answer']}")

                        st.write(f"Explanation: {item['explanation']}")





# ---------------- STUDY PROGRESS ----------------

elif page == "📈 Study Progress":

    render_hero("Study Progress", "Track quiz performance and identify recurring mistakes.")

    attempts = get_attempts()



    if not attempts:

        st.info("No quiz history yet. Complete a practice quiz to see your progress here.")

    else:

        c1, c2, c3 = st.columns(3)

        c1.metric("Quizzes completed", len(attempts))

        average = sum(a["percentage"] for a in attempts) / len(attempts)

        c2.metric("Average score", f"{average:.1f}%")

        c3.metric("Questions attempted", sum(a["total_questions"] for a in attempts))



        st.subheader("Performance Over Time")

        chart_data = pd.DataFrame(attempts)

        chart_data["created_at"] = pd.to_datetime(

            chart_data["created_at"], errors="coerce"

        )

        chart_data = chart_data.dropna(subset=["created_at"]).sort_values("created_at")

        if not chart_data.empty:

            chart = px.line(

                chart_data,

                x="created_at",

                y="percentage",

                markers=True,

                title="Quiz score trend",

                labels={"created_at": "Attempt date", "percentage": "Score (%)"},

                hover_data=["document_name", "score", "total_questions"],

            )

            chart.update_yaxes(range=[0, 100])

            chart.update_layout(

                template="plotly_white",

                margin=dict(l=20, r=20, t=50, b=20),

            )

            st.plotly_chart(chart, use_container_width=True)



        st.subheader("Quiz History")

        history = pd.DataFrame(attempts).rename(columns={

            "document_name": "Document",

            "total_questions": "Questions",

            "score": "Correct",

            "percentage": "Score (%)",

            "created_at": "Date",

        })

        st.dataframe(

            history[["Date", "Document", "Questions", "Correct", "Score (%)"]],

            use_container_width=True,

            hide_index=True,

        )



        # Topic-based review section. Only incorrect answers are recorded,

        # so counts represent mistakes, not an accuracy percentage.

        st.subheader("Topics to Review")

        weak_topics = get_weak_topics()



        if weak_topics:

            st.caption(

                "Topics are ranked by the number of incorrect answers "

                "across your saved quiz attempts. Older attempts without "

                "topic labels may appear as Uncategorized."

            )

            topic_df = pd.DataFrame(weak_topics)

            topic_df = topic_df.rename(columns={

                "topic": "Topic",

                "incorrect_attempts": "Incorrect answers",

                "unique_questions": "Distinct questions missed",

            })

            st.dataframe(topic_df, use_container_width=True, hide_index=True)



            for item in weak_topics:

                with st.expander(

                    f"{item['topic']} — {item['incorrect_attempts']} incorrect answer(s)"

                ):

                    st.write(

                        f"You have missed {item['unique_questions']} distinct "

                        f"question(s) associated with **{item['topic']}**."

                    )

                    st.write(

                        f"Recommendation: revise **{item['topic']}** in your PDF, "

                        "then generate another quiz to check your understanding."

                    )

        else:

            st.success(

                "No incorrect answers recorded yet. Complete and submit a quiz "

                "with at least one incorrect answer to populate this section."

            )



        st.subheader("Frequently Missed Questions")

        weak_questions = get_weak_questions()

        if weak_questions:

            for item in weak_questions:

                with st.expander(

                    f"{item['question']} ({item['wrong_count']} incorrect attempt(s))"

                ):

                    st.write(f"Topic: {item.get('topic', 'Uncategorized')}")

                    st.write(

                        "Recommendation: revisit the related section in your "

                        "study PDF and practise this concept again."

                    )

        else:

            st.caption("No repeated mistakes recorded yet.")



        st.divider()

        with st.expander("Clear quiz history"):

            st.warning("This permanently deletes saved quiz attempts from the local database.")

            confirm = st.checkbox(

                "I understand that this action cannot be undone.",

                key="confirm_clear_history",

            )

            if st.button("Delete All Quiz History", disabled=not confirm):

                clear_history()

                st.success("Quiz history deleted.")

                st.rerun()
