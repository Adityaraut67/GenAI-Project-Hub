from fastapi import APIRouter
from src.controllers.ans import ans
from src.controllers.make_session import set_session
from yt_dlp import YoutubeDL

router = APIRouter()

router.get("/set-session")(set_session)

router.get("/ans")(ans)