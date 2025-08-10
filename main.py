from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
from database import SessionLocal, engine
import models, schemas, crud

import os
from utils.token import create_access_token
from fastapi.middleware.cors import CORSMiddleware


SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# FastAPI uygulaması
app = FastAPI(title="LawBridge API", description="Hukuki yorum analizi sistemi")

# CORS ayarları
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # * kullanma; spesifik origin yaz
    allow_credentials=True,     # ileride cookie kullanırsan da çalışsın
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== AUTHENTİCATİON ENDPOINTS ==========

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    new_user = crud.create_user(db, user)
    access_token = create_access_token(data={"user_id": new_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
    }


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    auth_user = crud.authenticate_user(db, user.email, user.password)
    if not auth_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz e-posta veya şifre")

    access_token = create_access_token(data={"user_id": auth_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": auth_user.id,
            "username": auth_user.username,
            "email": auth_user.email
        }
    }


@app.post("/token", response_model=schemas.TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz kimlik bilgileri")

    access_token = create_access_token(data={"user_id": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }


@app.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ========== AYARLAR ENDPOINTS ==========

@app.post("/update_preferences")
def update_preferences(
    prefs: schemas.PreferencesResponse,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    updated = crud.update_or_create_settings(
        db,
        user_id=current_user.id,
        mode=prefs.mode,
        frequency=prefs.frequency,
        platform=prefs.platform
    )
    return {
        "status": "success",
        "data": {
            "mode": updated.mode,
            "frequency": updated.frequency,
            "platform": updated.platform
        }
    }


@app.get("/get_preferences")
def get_preferences(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prefs = crud.get_user_preferences(db, current_user.id)
    if not prefs:
        raise HTTPException(status_code=404, detail="Kullanıcıya ait ayar bulunamadı")
    return {
        "mode": prefs.mode,
        "platform": prefs.platform,
        "frequency": prefs.frequency
    }


# ========== ANALİZ ENDPOINTS ==========

@app.post("/create_analysis")
def create_analysis(
    request: schemas.CreateAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    crud.create_analysis(
        db=db,
        user_id=current_user.id,
        analysis_name=request.analysis_name,
        platform=request.platform,
        mode=request.mode,
        frequency=request.frequency,
        data=request.data
    )
    return {"message": "Analiz başarıyla oluşturuldu"}


# ⭐ FRONTEND'İN BEKLEDİĞİ ANA ENDPOINT
@app.get("/analyses", response_model=schemas.DashboardResponse)
def get_analyses_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Frontend dashboard için ana veri endpoint'i"""
    return crud.get_dashboard_data(db, current_user.id)


@app.get("/analysis_results", response_model=List[schemas.AnalysisSummary])
def get_user_analyses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Kullanıcının analiz listesi"""
    return crud.get_user_analysis_results(db=db, user_id=current_user.id)


@app.get("/analysis_results/{analysis_id}", response_model=schemas.AnalysisDetailResponse)
def get_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Belirli bir analizin detaylarını getirir"""
    return crud.get_analysis_by_id(db=db, user_id=current_user.id, analysis_id=analysis_id)


@app.get("/filter_analysis_results", response_model=List[schemas.AnalysisSummary])
def filter_analyses(
    platform: Optional[str] = None,
    mode: Optional[str] = None,
    frequency: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Analizleri filtreler"""
    return crud.filter_analysis_results(
        db=db,
        user_id=current_user.id,
        platform=platform,
        mode=mode,
        frequency=frequency
    )


@app.get("/search_analysis", response_model=List[schemas.AnalysisSummary])
def search_analysis_by_name(
    query: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Analiz adına göre arama"""
    return crud.search_analysis_by_name(db=db, user_id=current_user.id, query=query)


@app.get("/analysis_distribution/{analysis_id}")
def get_analysis_distribution(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Belirli bir analiz için etiket dağılımı"""
    return crud.get_label_distribution(
        db=db,
        user_id=current_user.id,
        analysis_id=analysis_id
    )