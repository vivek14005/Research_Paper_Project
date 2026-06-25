from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.models.user import User
from app.agents.research_agent import research_agent_system
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    paper_ids: List[str]
    summary_type: Optional[str] = "technical"

class ChatResponse(BaseModel):
    response: str
    context_used: Optional[str] = None

@router.post("/", response_model=ChatResponse)
async def chat_with_papers(
    request: ChatRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    # In a real app, we'd verify current_user owns these paper_ids
    
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "paper_ids": request.paper_ids,
        "summary_type": request.summary_type,
        "context": "",
        "analysis_results": {}
    }
    
    try:
        result = await research_agent_system.graph.ainvoke(initial_state)
        last_message = result["messages"][-1]
        
        return ChatResponse(
            response=last_message.content,
            context_used=result.get("context")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
