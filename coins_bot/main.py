from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI()

# CORS для Telegram
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для обхода предупреждения ngrok
@app.middleware("http")
async def add_ngrok_skip_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# Подключаем статические файлы
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/coins"):
    os.makedirs("static/coins")
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/", response_class=HTMLResponse)
async def get_mini_app():
    with open("index.html", "r", encoding="utf-8") as file:
        return file.read()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)