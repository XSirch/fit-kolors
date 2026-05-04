from typing import Dict, List, Optional

from pydantic import BaseModel


class DetectedColors(BaseModel):
    skin: str
    hair: str
    eyes: str
    lips: str


class AnalysisDetail(BaseModel):
    season: str
    undertone: str
    contrast: str
    depth: str
    metals: List[str]
    explanation: str


class SeasonPalette(BaseModel):
    theory: str
    day: List[str]
    night: List[str]


class MakeupTips(BaseModel):
    lipstick: str
    blush: str
    eyeshadow: str


class MakeupColors(BaseModel):
    lipstick: List[str]
    blush: List[str]
    eyeshadow: List[str]
    foundation_undertone: str


class HairRecommendations(BaseModel):
    recommended_tones: List[str]
    highlights: List[str]
    notes: str


class ColorToAvoid(BaseModel):
    hex: str
    reason: str


class ColorAnalysisResponse(BaseModel):
    model_version: str
    confidence: float
    photo_flags: List[str]
    detected_colors: DetectedColors
    analysis: AnalysisDetail
    recommendations: Dict[str, SeasonPalette]
    makeup_tips: MakeupTips
    makeup: MakeupColors
    hair: HairRecommendations
    colors_to_avoid: List[ColorToAvoid]


class WebhookJobAccepted(BaseModel):
    job_id: str
    status: str
    queue: str
    webhook_url: str


class WebhookEvent(BaseModel):
    event: str
    job_id: str
    status: str
    created_at: str
    completed_at: str
    result: Optional[ColorAnalysisResponse] = None
    error: Optional[str] = None
