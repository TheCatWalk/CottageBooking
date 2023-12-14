from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/rdg1")
async def get_rdg1():
    with open("rdg1.ttl", "r") as file:
        return PlainTextResponse(file.read())

@app.get("/rdg2")
async def get_rdg2():
    with open("rdg2.ttl", "r") as file:
        return PlainTextResponse(file.read())

# Run this app with `uvicorn fake_service:app --reload --port 8001` and `--port 8002` for each service
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5002)
