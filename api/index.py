from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(executor, find_nba_video_clip, query),
                    timeout=SEARCH_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail=f"Search timed out after {SEARCH_TIMEOUT_SECONDS} seconds"
                )

        return result
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"ok": True}
