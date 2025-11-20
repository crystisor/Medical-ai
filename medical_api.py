from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

# ---- CONFIG ----
LOCAL_LLM_URL = "http://localhost:11434/api/generate"

# ---- ROUTER ----
llm_router = APIRouter()

# ---- REQUEST BODY MODEL ----
class PromptRequest(BaseModel):
    question: str

# ---- ENDPOINT ----
@llm_router.post("/ask")
def ask_llm(request: PromptRequest):
    """
    Receives question from your app,
    sends it to the local AI,
    returns AI answer immediately.
    """
    payload = {
        "model": "medical:ai",
        "prompt": request.question,
        "stream": False
    }
    try:
        llm_response = requests.post(LOCAL_LLM_URL, json=payload)
        llm_response.raise_for_status()
        llm_data = llm_response.json()
        answer = llm_data.get("response", "").strip()
        if not answer:
            answer = "The AI returned an empty response."
        return {"answer": answer}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Local LLM could not be reached: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")