from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app import find_nba_video_clip
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
import asyncio

app = FastAPI(title="NBA Video Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global timeout for entire search operation (60 seconds)
SEARCH_TIMEOUT_SECONDS = 60

class SearchRequest(BaseModel):
    query: str

@app.post("/api/search")
async def search(request: SearchRequest):
    start_time = time.time()
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Missing query")

        print(f"[FastAPI] Received search request for: '{query}'")
        
        # Run the blocking function in a thread pool with timeout
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(executor, find_nba_video_clip, query),
                    timeout=SEARCH_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                end_time = time.time()
                print(f"[FastAPI] Search '{query}' timed out after {end_time - start_time:.2f} seconds")
                raise HTTPException(
                    status_code=504, 
                    detail=f"Search timed out after {SEARCH_TIMEOUT_SECONDS} seconds. Please try again."
                )
        
        end_time = time.time()
        print(f"[FastAPI] Search '{query}' completed in {end_time - start_time:.2f} seconds")
        print(f"[FastAPI] Result success: {result.get('success', False)}, clips count: {len(result.get('clips', []))}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        end_time = time.time()
        print(f"[FastAPI] Search failed after {end_time - start_time:.2f} seconds: {str(e)}")
        print(traceback.format_exc())
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

