from langchain_core.documents import Document
from src.utils.create_llm import tokenizer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder=os.path.join(os.getcwd(),"embedding_model")
)

vector_db = Chroma(
    collection_name="youtube_transcripts",
    embedding_function=embedding,
    persist_directory=os.path.join(os.getcwd(),"db/vector_db","chroma_db")
)

def create_documents(transcript):
    docs=[]
    for t in transcript:
        docs.append(
            Document(
                page_content=t["text"],
                metadata={
                    "video_id":t["video_id"],
                    "start":t["start"],
                    "end":t["end"]
                }
            )
        )
    return docs

splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    tokenizer=tokenizer,
    chunk_size=256,
    chunk_overlap=32
)

def split_transcript(transcript):
    docs = create_documents(transcript)
    docs_chunks = splitter.split_documents(docs)
    return docs_chunks


def save_transcript(transcript,video_id):
    docs_chunks = split_transcript(transcript)
    vector_db.add_documents(docs_chunks)
    return video_id

def already_have_transcript(video_id):
    result = vector_db.get(
        where = {
            "video_id":video_id
        },
        include=[]
    )

    return len(result["ids"])>0

def get_context_transcript(video_id,query,top_k):
    result = vector_db.similarity_search(
        query,
        k=top_k,
        filter={
            "video_id":video_id
        }
    )
    chunk_number=1
    context=""

    for doc in result:
        context+=f"""
chunk: {chunk_number}
start: {doc.metadata["start"]}
end: {doc.metadata["end"]}
{doc.page_content}

"""
        chunk_number+=1

    return context