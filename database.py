from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# .env dosyasını yükle (örn. DATABASE_URL okunabilsin diye)
load_dotenv()

# .env dosyasındaki DATABASE_URL alınır
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy veritabanı motoru oluşturulur
engine = create_engine(DATABASE_URL)

# Oturum oluşturucu (session factory)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Model sınıflarının kalıtım alacağı temel sınıf
Base = declarative_base()

# Her istek için bağımsız bir veritabanı oturumu dönen fonksiyon (dependency injection için)
def get_db():
    db = SessionLocal()
    try:
        yield db # çağıran fonksiyona session nesnesi verilir
    finally:
        db.close() # iş bitince bağlantı kapatılır