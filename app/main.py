from fastapi import FastAPI
from app.api.v1.routes.auth import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def health_check():
    return{"status": "ok"}