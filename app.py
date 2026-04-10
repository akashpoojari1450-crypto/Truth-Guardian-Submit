from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.post("/reset")
def reset():
    return JSONResponse({"status": "ok"})

@app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})

@app.get("/")
def root():
    return {"status": "running", "project": "Truth Guardian Vakratunda"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
