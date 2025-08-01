from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from dependencies import get_current_user
from schemas import UserOut
from database import SessionLocal, engine
import models, schemas, crud
from utils.token import create_access_token

import os

# Ortam değişkenleri
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Veritabanı tabloları oluştur
models.Base.metadata.create_all(bind=engine)

# FastAPI uygulaması
app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Gerekirse sadece frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanı oturumu bağımlılığı
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Tercih güncelleme
@app.post("/update_preferences")
def update_preferences(prefs: schemas.PreferencesRequest, db: Session = Depends(get_db)):
    updated = crud.update_or_create_settings(
        db,
        user_id=prefs.user_id,
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

# Tercih alma (Token ile kimlik doğrulamalı)
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

# Kullanıcı kaydı
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    new_user = crud.create_user(db, user)
    return {"status": "success", "user_id": new_user.id}

# Login – JWT döner
@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    auth_user = crud.authenticate_user(db, user.email, user.password)
    if not auth_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz e-posta veya şifre")

    access_token = create_access_token(data={"sub": str(auth_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": auth_user.id,
        "username": auth_user.username,
        "email": auth_user.email
    }

# OAuth2 için token endpointi
@app.post("/token", response_class=JSONResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz kimlik bilgileri")
    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

# Giriş yapmış kullanıcı bilgisi
@app.get("/me", response_model=UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
