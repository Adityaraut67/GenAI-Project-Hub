from src.utils.get_transcript import get_available_transcript_language,get_transcript
from src.utils.rag import get_context_transcript
from src.llm.transcript_ans_llm import transcript_ans

async def ans(video_id:str | None, query:str | None):
    print(video_id,query)
    context = get_context_transcript(video_id,query,3)
    response = transcript_ans(context,query)

    return {"data":response}