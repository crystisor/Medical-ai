from fastapi import FastAPI
import uvicorn

# Import routers from your other files
from medical_api import llm_router
from comfyUI_api import comfyui_router

app = FastAPI()

# Include the routers in your main app
app.include_router(llm_router, tags=["Local LLM"])
app.include_router(comfyui_router, tags=["ComfyUI Image Generation"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the integrated AI server. Visit /docs for API documentation."}

if __name__ == "__main__":
    print("Starting FastAPI server. Access it at http://127.0.0.1:5000")
    print("Or via ngrok if you have it running (e.g., `ngrok http 5000`)")
    print("API documentation available at http://127.0.0.1:5000/docs")
    uvicorn.run(app, host="0.0.0.0", port=5000)
