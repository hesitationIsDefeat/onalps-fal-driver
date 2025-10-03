from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import fal_client
import uvicorn
import os

app = FastAPI()

load_dotenv()

# Request schema
class GenerateRequest(BaseModel):
    prompt: str
    image_urls: List[str]

# Response schema
class GenerateResponse(BaseModel):
    urls: List[str]

@app.post(os.getenv("GENERATE_ENDPOINT"), response_model=GenerateResponse)
async def generate(data: GenerateRequest):
    # Call fal_client workflow
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(f"[LOG] {log.get('message')}")

    result = await fal_client.subscribe_async(
        os.getenv("FAL_WORKFLOW_URL"),
        arguments={
            os.getenv("PROMPT_PARAMETER"): data.prompt,
            os.getenv("IMAGE_URLS_PARAMETER"): data.image_urls,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    # Extract image URLs
    urls = [img[os.getenv("IMAGE_RESPONSE_FIELD")] for img in result.get(os.getenv("IMAGES_RESPONSE_FIELD"), []) if "url" in os.getenv("IMAGE_RESPONSE_FIELD")]
    return GenerateResponse(urls=urls)

    return GenerateResponse(urls=urls)

# Run with: uvicorn main:app --reload --port 8087
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8087, reload=True)
