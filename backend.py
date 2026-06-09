import os 
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from  agent import workflow
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aegis-ui-l596.onrender.com","http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class initial(BaseModel):
    topic: str
    audience: Optional[str] = "General Public"
    tone: Optional[str] = "Professional"

@app.post("/app/call")
async def agent_call(request: InitialRequest):
    try:
        initial_state={
            "User_query": request.topic,
            "audience": request.audience,
            "tone": request.tone
        }
        final_state=workflow.invoke(initial_state)
        sections=final_state.get("article_section",[])
        if not sections:
            raise HTTPException(status_code=500, detail="Agent failed to generate sections.")
        return {
            "status": "success",
            "data": sections
        }
    except:
        raise HTTPException(status_code=500, detail=str(e))
