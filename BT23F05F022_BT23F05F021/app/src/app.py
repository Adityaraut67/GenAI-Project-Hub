from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.routers.router import router
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allows all origins
    allow_credentials=False,   # Must be False if allow_origins=["*"]
    allow_methods=["*"],       # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],       # Allows all headers
)

app.mount(
    "/public",
    StaticFiles(directory="app/src/public",html=True),
    name="public"
)

@app.get("/")
async def home():
    return FileResponse("app/src/public/index.html")

app.include_router(
    router,
    prefix="/api",
    tags=["API Entry point"]
)