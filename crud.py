from sqlalchemy.orm import Session
from models import Settings, User
from passlib.context import CryptContext
import schemas  # ✅ Eksik olan buydu

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def update_or_create_settings(db: Session, user_id: int, mode: str, frequency: str, platform: str):
    settings = db.query(Settings).filter(Settings.user_id == user_id).first()

    if settings:
        settings.mode = mode
        settings.frequency = frequency
        settings.platform = platform
    else:
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

def get_user_preferences(db: Session, user_id: int):
    return db.query(Settings).filter(Settings.user_id == user_id).first()

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
#
# def authenticate_user(db: Session, email: str, password: str):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         return None
#     if not pwd_context.verify(password, user.password):
#         return None
#     return user
