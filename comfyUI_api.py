from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
import json
import urllib.request
import urllib.parse
import websocket
import base64

# ---- CONFIG ----
COMFYUI_URL = "http://127.0.0.1:8000"
WORKFLOW_FILE = "workflow.json"
PROMPT_NODE_ID = "6"
OUTPUT_NODE_ID = "9"

# ---- ROUTER ----
comfyui_router = APIRouter()

# ---- REQUEST BODY MODEL ----
class ImagePromptRequest(BaseModel):
    prompt: str

# ---- COMFYUI CLIENT ----
def queue_prompt(prompt, client_id):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{COMFYUI_URL}/view?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_images(ws, prompt, client_id, output_node_id):
    prompt_id = queue_prompt(prompt, client_id)['prompt_id']
    output_images = {}
    
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            continue #previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for o in history['outputs']:
        if o == output_node_id:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                if 'images' in node_output:
                    images_output = []
                    for image in node_output['images']:
                        image_data = get_image(image['filename'], image['subfolder'], image['type'])
                        images_output.append(image_data)
                output_images[node_id] = images_output

    return output_images

# ---- ENDPOINT ----
@comfyui_router.post("/generate-image")
def generate_image(request: ImagePromptRequest):
    """
    Receives a prompt, generates an image using ComfyUI,
    and returns the image as a base64 encoded string.
    """
    client_id = str(uuid.uuid4())
    
    try:
        with open(WORKFLOW_FILE, 'r') as f:
            prompt_workflow = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Workflow file '{WORKFLOW_FILE}' not found.")

    # Inject the prompt into the workflow
    prompt_workflow[PROMPT_NODE_ID]['inputs']['text'] = request.prompt
    
    ws = websocket.WebSocket()
    try:
        ws.connect(f"ws://{COMFYUI_URL.split('//')[1]}/ws?clientId={client_id}")
        images = get_images(ws, prompt_workflow, client_id, OUTPUT_NODE_ID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect or get image from ComfyUI: {e}")
    finally:
        ws.close()

    if not images:
        raise HTTPException(status_code=500, detail="Image generation failed, no output from ComfyUI.")

    # Assuming you want the first image from the output node
    image_data = next(iter(images.values()))[0]

    # Encode image data to base64
    base64_image = base64.b64encode(image_data).decode('utf-8')

    return JSONResponse(content={
        "image_base64": base64_image,
        "format": "png" # Assuming PNG, adjust if necessary
    })
