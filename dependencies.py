from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import models
from utils.token import SECRET_KEY, ALGORITHM
from database import get_db

# Swagger UI'da "Authorize" butonunun çalışması için tokenUrl "token" olmalı
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Giriş yapan kullanıcının kimliğini doğrulayan fonksiyon
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Kimlik doğrulama başarısız olursa verilecek standart hata
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # Token çözülür (decode edilir)
        user_id: int = payload.get("user_id") # Payload'dan user_id alınır
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Veritabanında bu user_id ile eşleşen kullanıcı aranır
    user = db.query(models.User).filter(models.User.id == user_id).first()

    print("🔐 Gelen Token:", token)
    print("🔓 Çözülmüş Payload:", payload)
    print("🔍 Aranan user_id:", user_id)
    print("📁 DB'den Gelen User:", user)

    if user is None:
        raise credentials_exception
    return user # Başarıyla kimlik doğrulanan kullanıcı döndürülür
