from langchain_core.prompts import ChatPromptTemplate
from src.utils.create_llm import create_llm

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert YouTube transcript question-answering assistant.

Answer the user's question using ONLY the provided YouTube video transcript.

Rules:
- Use only the information present in the transcript.
- Do not use your own knowledge or make assumptions.
- Do not hallucinate or invent information.
- If the answer is not present in the transcript, reply exactly:
  "Sorry, I don't know. The provided transcript does not contain the answer."

YouTube Video Transcript:
-------------------------
{transcript}
-------------------------
"""
        ),
        (
            "human",
            """
Question:
{question}
"""
        ),
    ]
)


llm = create_llm()

def transcript_ans(context,query):
    chain = prompt | llm
    return chain.invoke({"transcript":context,"question":query})