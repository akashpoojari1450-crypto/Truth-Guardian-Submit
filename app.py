from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/reset")
def reset():
    return JSONResponse({"status": "ok", "message": "reset successful"})

@app.get("/")
def root():
    return {"status": "running", "project": "Truth Guardian Vakratunda"}
