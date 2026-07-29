from fastapi import FastAPI
from app.api.v1.routes.auth import auth_router
from app.api.v1.routes.users import user_router
from app.api.v1.routes.products import router as product_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(product_router)


@app.get("/")
def health_check():
    return{"status": "ok"}