from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

# ---- CONFIG ----
# Change this if he's using LM Studio instead of Ollama
LOCAL_LLM_URL = "http://localhost:11434/api/generate"


# ---- REQUEST BODY MODEL ----
class PromptRequest(BaseModel):
    question: str


# ---- MAIN ENDPOINT ----
@app.post("/ask")
def ask_llm(request: PromptRequest):
    """
    Receives question from your app,
    sends it to the local AI,
    returns AI answer immediately.
    """

    # Format for Ollama-style API
    payload = {
        "model": "medical:ai",  # Change if needed
        "prompt": request.question,
        "stream": False
    }

    try:
        # Call local model
        llm_response = requests.post(LOCAL_LLM_URL, json=payload)
        llm_data = llm_response.json()

        # Extract the answer (Ollama uses 'response')
        answer = llm_data.get("response", "").strip()

        if not answer:
            answer = "The AI returned an empty response."

        # Return answer directly to your app
        return {
            "answer": answer
        }

    except Exception as e:
        print("LLM error:", e)
        return {
            "answer": None,
            "error": f"Local model could not be reached: {e}"
        }