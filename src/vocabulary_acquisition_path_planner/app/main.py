from fastapi import FastAPI

app = FastAPI(title="API Lecture et Vocabulaire")


@app.get("/api/ping")
def ping():
    return {"message": "pong"}