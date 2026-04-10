import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/reset")
def reset():
    return JSONResponse({"status": "ok"})

@app.get("/health")
def health():
    return JSONResponse({"status": "healthy"})

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
