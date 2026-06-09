import os 
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from  agent import workflow
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional,Literal
from dotenv import load_dotenv
import traceback
load_dotenv()

app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://newsletter-agent-jvvq.onrender.com","http://localhost:3000","http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class initial(BaseModel):
    topic: str
    audience: Optional[str] = "General Public"
    tone: Optional[str] = "Professional"
    length:Literal["short", "medium", "long"]
    key_points:Optional[str]=None

@app.post("/api/v1/generate")
async def agent_call(request:initial):
    try:
        initial_state={
            "User_query": request.topic,
            "audience": request.audience,
            "tone": request.tone,
            "length":request.length,
            "key_points":request.key_points
        }
        final_state=await workflow.ainvoke(initial_state)
        sections=final_state.get("article_sections",[])
        if not sections:
            raise HTTPException(status_code=500, detail="Agent failed to generate sections.")
        return {
            "status": "success",
            "data": sections
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500,detail=str(e))
