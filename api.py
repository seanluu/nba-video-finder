from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app import find_nba_video_clip
import time

app = FastAPI(title="NBA Video Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str

@app.post("/api/search")
async def search(request: SearchRequest):
    start_time = time.time()
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Missing query")

        result = find_nba_video_clip(query)
        end_time = time.time()
        print(f"Search '{query}' took {end_time - start_time:.2f} seconds")
        return result
    except Exception as e:
        end_time = time.time()
        print(f"Search failed after {end_time - start_time:.2f} seconds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"ok": True}

@app.get("/")
async def index():
    return {"message": "NBA Video Finder API"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)