from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from pydantic.config import ConfigDict


# Kullanıcı ayarları için models
class PreferencesResponse(BaseModel):
    mode: str
    platform: str
    frequency: Optional[str] = None


# Kullanıcı kaydı ve girişi için models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


# Token modeli
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    email: str


# Yorum analizi için modeller
class CommentAnalysisItem(BaseModel):
    comment: str
    labels_hukuk: Optional[List[str]] = None  # ['a', 's', 'd'] gibi
    labels_duygu: Optional[List[str]] = None  # ['1', '2', '3'] gibi
    labels_niyet: Optional[List[str]] = None  # ['6', '7', 'q'] gibi
    temizlik: Optional[str] = None  # 'p', 'j', 'k'
    law_score: Optional[float] = None  # 0.0 - 1.0


# Yeni analiz oluşturma isteği
class CreateAnalysisRequest(BaseModel):
    analysis_name: str
    platform: str
    mode: str
    frequency: Optional[str] = None
    data: List[CommentAnalysisItem]


# Content item modeli
class ContentItemResponse(BaseModel):
    id: int
    platform: str
    content_id: str
    content_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Yorum modeli
class CommentResponse(BaseModel):
    id: int
    text: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# Analiz sonucu modeli
class AnalysisResultResponse(BaseModel):
    id: int
    comment_id: int
    labels_hukuk: Optional[List[str]] = None
    labels_duygu: Optional[List[str]] = None
    labels_niyet: Optional[List[str]] = None
    temizlik: Optional[str] = None
    law_score: Optional[float] = None
    has_dilekce: bool
    created_at: datetime

    # İlişkili yorum verisini de döndür
    comment: CommentResponse

    model_config = ConfigDict(from_attributes=True)


# Frontend dashboard için analiz özeti
class AnalysisSummary(BaseModel):
    id: int
    name: str  # content_id'den türetilecek
    date: str  # created_at'dan formatlanacak
    platform: str
    mode: Optional[str] = None
    frequency: Optional[str] = None
    total_comments: int
    analyzed_comments: int


# Dashboard ana response
class DashboardResponse(BaseModel):
    total_comments: int
    analyzed_comments: int
    duygu_distribution: Dict[str, int]
    niyet_distribution: Dict[str, int]
    hukuki_distribution: Dict[str, int]
    analyses: List[AnalysisSummary]


# Analiz detayı için response
class AnalysisDetailResponse(BaseModel):
    analysis_info: AnalysisSummary
    comments: List[AnalysisResultResponse]
    distribution: Dict[str, Dict[str, int]]


# Dilekçe log modeli
class DilekceLogResponse(BaseModel):
    id: int
    analysis_id: int
    generated_text: str
    pdf_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)