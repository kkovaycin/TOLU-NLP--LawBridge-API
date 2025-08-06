from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserOut

from database import SessionLocal, engine
import models, schemas, crud

import os
from utils.token import create_access_token

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

# FastAPI uygulaması
app = FastAPI()

# CORS ayarları – tarayıcıdan gelen fetch() istekleri için gerekli
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    # allow_origins=["*"],  # Gerekirse burada sadece senin frontend URL'in olur
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Her endpoint'te çağrılabilecek veritabanı oturumu fonksiyonu
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Kullanıcı tercihlerini kaydeden endpoint
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

# Yeni kullanıcı kaydeden endpoint
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print("Gelen kullanıcı:", user)


    # Aynı e-posta ile kayıtlı kullanıcı var mı kontrol et
    existing_user = db.query(models.User).filter(user.email == models.User.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    # Yeni kullanıcı oluşturulur (Burada veritabanına kullanıcıyı yazıyor)
    new_user = crud.create_user(db, user)
    # access_token = create_access_token(data={"sub": str(new_user.id)})

    # JWT token oluşturulur
    access_token = create_access_token(data={"user_id": new_user.id})

    return {"access_token": access_token,
            "token_type": "bearer",
            "user_id": new_user.id,
            "username": new_user.username,
            "email": new_user.email}


# Kullanıcı girişi yapan endpoint
@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    #  Bu satırda crud.py dosyasındaki authenticate_user fonksiyonu çağrılıyor.
    # Amaç: Veritabanındaki kullanıcıyı bulmak ve şifrenin doğru olup olmadığını kontrol etmek.
    auth_user = crud.authenticate_user(db, user.email, user.password)
    if not auth_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz e-posta veya şifre")

    access_token = create_access_token(data={"user_id": auth_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": auth_user
    }

# OAuth2 login endpoint (Swagger UI ile giriş için)
@app.post("/token", response_model=schemas.TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz kimlik bilgileri")

    access_token = create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "username": user.username,
            "email": user.email}

# Giriş yapan kullanıcının bilgilerini döndürür
@app.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
