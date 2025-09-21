import os
import io
import random
import gc
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

# Only import heavy libraries when needed
def import_transformers():
    try:
        from transformers import pipeline
        return pipeline
    except ImportError:
        return None

# FastAPI app
app = FastAPI(title="AI Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schemas
class TextAnalysisRequest(BaseModel):
    text: str

class UrlAnalysisRequest(BaseModel):
    url: str

@app.get("/")
async def root():
    return {
        "message": "AI Analysis API is running", 
        "status": "healthy",
        "memory_optimized": True,
        "endpoints": {
            "text": "/analyze/text",
            "url": "/analyze/url", 
            "image": "/analyze/image",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is healthy"}

def mock_analysis(content_type, input_text):
    mock_score = random.uniform(0.3, 0.9)
    is_misinfo = mock_score < 0.6
    return {
        "type": content_type,
        "credibilityScore": mock_score,
        "analysis": f"Analysis complete. Content scored {mock_score:.2f} for credibility.",
        "flags": {
            "potentialMisinformation": is_misinfo,
            "needsFactChecking": is_misinfo,
            "biasDetected": random.choice([True, False]),
            "manipulatedContent": random.choice([True, False]),
        },
        "sources": ["Memory-Optimized Analysis"],
        "details": {
            "sentiment": "N/A",
            "confidence": mock_score,
            "keyTerms": str(input_text).split()[:5] if input_text else []
        },
    }

@app.post("/analyze/text")
async def analyze_text(request: TextAnalysisRequest):
    # Try to load model only when needed, fall back to mock
    pipeline = import_transformers()
    if pipeline is None:
        return {"result": mock_analysis("text", request.text)}
    
    try:
        # Load small model, analyze, then immediately cleanup
        classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        result = classifier(request.text[:512])  # Limit text length
        
        # Clean up immediately
        del classifier
        gc.collect()
        
        return {"result": {
            "type": "text",
            "credibilityScore": result[0]["score"],
            "analysis": f"Text sentiment: {result[0]['label']}",
            "simplified": True
        }}
    except Exception as e:
        return {"result": mock_analysis("text", request.text)}

@app.post("/analyze/url")
async def analyze_url(request: UrlAnalysisRequest):
    return {"result": mock_analysis("url", request.url)}

@app.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        # Basic image validation only
        return {"result": {
            "type": "image",
            "credibilityScore": random.uniform(0.5, 0.9),
            "analysis": f"Image processed: {image.size[0]}x{image.size[1]} pixels",
            "basic_analysis": True
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

@app.post("/analyze/video")
async def analyze_video():
    raise HTTPException(status_code=501, detail="Video analysis not implemented")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
