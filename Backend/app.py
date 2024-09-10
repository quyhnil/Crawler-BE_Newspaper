import os
from sqlite3 import connect, Row
from typing import List
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from database import decrease_summary_with_gemini, edit_summary_with_gemini, get_newspapers, get_summary, increase_summary_with_gemini, initialize_twitter_client, post_to_twitter
from fastapi.middleware.cors import CORSMiddleware

class TweetContent(BaseModel):
    id: int
    content: str

class EditSummaryRequest(BaseModel):
    id: int
    summary: str
    instruction: str

class DecreaseSummaryRequest(BaseModel):
    id: int
    summary: str

class IncreaseSummaryRequest(BaseModel):
    summary_text: str
    expansion: int

class TwitterKeys(BaseModel):
    api_key: str
    api_secret: str
    bearer_token: str
    access_token: str
    access_token_secret: str

app = FastAPI()

database_path = os.getenv('DATABASE_PATH', '/app/data/content.db')
connection = connect(database_path)
connection.row_factory = Row 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/twitter-keys")
async def twitter_api_keys(keys: TwitterKeys):
    try:
        initialize_twitter_client(
            keys.api_key,
            keys.api_secret,
            keys.bearer_token,
            keys.access_token,
            keys.access_token_secret
        )
        return {"message": "Twitter API keys updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/newspapers")
async def newspapers(limit: int = Query(5), page: int = Query(0)):
    items = get_newspapers(connection, limit=limit, page=page)
    has_more = len(items) == limit  
    return {"items": items, "has_more": has_more}

@app.post("/post-to-twitter")
def create_tweet(tweet: TweetContent):
    result = post_to_twitter(tweet.content)
    if result["success"]:
        return {"success": True, "message": "Tweet posted successfully"}
    else:
        return {"success": False, "message": "Failed to post tweet"}

@app.post("/edit-summary")
async def edit_summary(request: EditSummaryRequest):
    try:
        edited_summary = edit_summary_with_gemini(request.summary, request.instruction)
        return {"editedSummary": edited_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/decrease-text")
async def decrease_summary(request: DecreaseSummaryRequest):
    try:
        decrease_summary = decrease_summary_with_gemini(request.summary, 10)
        return {"decreaseSummary": decrease_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/increase-summary")
async def increase_summary(request: IncreaseSummaryRequest):
    try:
        increased_summary = increase_summary_with_gemini(request.summary_text, request.expansion)
        return {"increasedSummary": increased_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to the Newspaper API"}