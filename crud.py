from sqlalchemy.orm import Session

import models
from models import Settings, User
from passlib.context import CryptContext
import schemas

# Şifreleme için bcrypt algoritması kullanılır
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Kullanıcının ayarları güncellenir veya yeni ayar oluşturulur
def update_or_create_settings(db: Session, user_id: int, mode: str = None, frequency: str = None, platform: str = None):
    # Default değerler: boş geldiyse bile sistem çökmemeli
    mode = mode if mode else "düzensiz"
    platform = platform if platform else "X"  # varsayılan sosyal medya platformu
    frequency = frequency if frequency else None  # nullable olduğu için None olabilir

    settings = db.query(Settings).filter(Settings.user_id == user_id).first()

    if settings:
        # Ayar daha önce varsa güncelle
        settings.mode = mode
        settings.frequency = frequency
        settings.platform = platform
    else:
        # Ayar yoksa oluştur
        settings = Settings(
            user_id=user_id,
            mode=mode,
            frequency=frequency,
            platform=platform
        )
        db.add(settings)

    db.commit()
    db.refresh(settings)
    return settings

# Kullanıcının ayarlarını getirir
def get_user_preferences(db: Session, user_id: int):
    return db.query(models.Settings).filter(models.Settings.user_id == user_id).first()


# Yeni kullanıcı oluşturur
def create_user(db: Session, user: schemas.UserCreate):
    hashed_pw = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Kullanıcının e-posta ve şifresini doğrular
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(email == User.email).first()
    if not user:
        return None
    if not pwd_context.verify(password, user.password):
        return None
    return user
