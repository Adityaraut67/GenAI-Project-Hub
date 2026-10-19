from src.utils.get_transcript import get_video_id
from src.utils.get_transcript import get_transcript
from langchain_core.documents import Document
from src.utils.rag import save_transcript,already_have_transcript

async def set_session(url:str | None):
    video_id = get_video_id(url)
    is_already_exist=already_have_transcript(video_id)

    if(is_already_exist):
        return {"video_id":video_id,"already_exist":True}
    
    transcript = get_transcript(video_id,"en")
    video_id= save_transcript(transcript,video_id)
    print(video_id)

    return {"video_id":video_id}
    