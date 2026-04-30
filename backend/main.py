from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from analyzer import ColorAnalyzer
import uvicorn

app = FastAPI(
    title="Fit-Kolors API",
    description="API RESTful para análise de colorimetria pessoal utilizando IA.",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for Structured Response
class DetectedColors(BaseModel):
    skin: str
    hair: str
    eyes: str
    lips: str

class AnalysisDetail(BaseModel):
    season: str
    undertone: str
    contrast: str
    metals: str
    explanation: str

class SeasonPalette(BaseModel):
    theory: str
    day: List[str]
    night: List[str]

class MakeupTips(BaseModel):
    lipstick: str
    blush: str
    eyeshadow: str

class ColorAnalysisResponse(BaseModel):
    detected_colors: DetectedColors
    analysis: AnalysisDetail
    recommendations: Dict[str, SeasonPalette]
    makeup_tips: MakeupTips

analyzer = ColorAnalyzer()

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "Fit-Kolors API",
        "endpoints": {
            "analysis": "/analyze [POST]",
            "docs": "/docs [GET]"
        }
    }

@app.post("/analyze", response_model=ColorAnalysisResponse, tags=["Analysis"])
async def analyze_image(file: UploadFile = File(...)):
    """
    Recebe uma imagem (upload) e retorna um dossiê completo de colorimetria pessoal.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo enviado deve ser uma imagem (jpeg, png).")
    
    try:
        contents = await file.read()
        result = await analyzer.analyze_face(contents)
        
        # O FastAPI validará automaticamente o 'result' contra o 'ColorAnalysisResponse'
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
