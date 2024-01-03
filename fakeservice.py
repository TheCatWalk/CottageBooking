from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

# Create a new FastAPI application instance
fake_service_app = FastAPI()

# Define the endpoint to serve rdg1.ttl
@fake_service_app.get("/rdg1")
async def get_rdg1():
    try:
        return FileResponse('rdg1.ttl', media_type='text/turtle')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="RDG1 file not found")

# Define the endpoint to serve rdg2.ttl
@fake_service_app.get("/rdg2")
async def get_rdg2():
    try:
        return FileResponse('rdg2.ttl', media_type='text/turtle')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="RDG2 file not found")

@fake_service_app.get("/rdg3")
async def get_rdg2():
    try:
        return FileResponse('rdg3.ttl', media_type='text/turtle')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="RDG2 file not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fake_service_app, host="127.0.0.1", port=8001)
