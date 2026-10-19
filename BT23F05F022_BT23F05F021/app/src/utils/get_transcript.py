from youtube_transcript_api import YouTubeTranscriptApi
import re

api = YouTubeTranscriptApi()

def get_video_id(url):
    if "youtu.be/" in url:
        pattern = r"youtu\.be/([A-Za-z0-9_-]{11})"
    elif "youtube.com/watch" in url:
        pattern = r"[?&]v=([A-Za-z0-9_-]{11})"
    else:
        return None

    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_available_transcript_language(video_id):
    transcripts = api.list(video_id)
    data = {}
    for t in transcripts:
        data[t.language]=t.language_code
    return data

def get_transcript(video_id,language):
    transcript = YouTubeTranscriptApi().fetch(video_id,languages=[language])
    transcript_format = []
    max_char=400
    count=0
    index=0
    transcript_format.append({"text":"","start":0,"end":0,"video_id":video_id})
    for t in transcript:
        if count+len(t.text)>max_char:
            count=0
            index+=1
            transcript_format.append({"text":t.text,"start":t.start,"end":t.start,"video_id":video_id})
        else:
            transcript_format[index]["text"]=transcript_format[index]["text"]+" "+t.text
            transcript_format[index]["end"]=transcript_format[index]["end"]+t.duration
        count+=len(t.text)
    return transcript_format
    