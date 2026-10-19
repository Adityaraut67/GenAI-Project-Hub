import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("HOST","127.0.0.1")
port = int(os.getenv("PORT",4000))

if __name__=="__main__":
    uvicorn.run(
        "src.app:app",
        host=host,
        port=port,
        reload=True
    )