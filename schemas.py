from pydantic import BaseModel, EmailStr
from typing import Optional


# Kullanıcıdan gelen tercih verileri için istek modeli
# class PreferencesRequest(BaseModel):
#     user_id: int
#     platform: str
#     mode: str
#     frequency: Optional[str] = None
#

# API'den dönen tercih verileri için cevap modeli
class PreferencesResponse(BaseModel):
    mode: str
    platform: str
    frequency: Optional[str] = None


# Yeni kullanıcı kaydı için model.
# Yeni kullanıcı oluşturulurken kullanılır (Register).
# API'ye gelen POST /register verisini temsil eder.
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


# Kullanıcı girişi için model.
# Giriş yaparken kullanılır (POST /login).
# Kullanıcıdan sadece e-posta ve şifre alır.
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Token doğrulaması yapılmış kullanıcıyı temsil eden çıktı modeli.
# JWT doğrulaması sonrası (örneğin /me endpoint'inde) kullanıcı bilgileri
# frontend’e dönerken kullanılır.
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True  # Pydantic v2 uyumu için


# Login sonrası dönen token yapısı
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
