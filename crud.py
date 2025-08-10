from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import models
from models import Settings, User, ContentItem, Comment, AnalysisResults
from passlib.context import CryptContext
import schemas
from collections import Counter
from fastapi import HTTPException
from datetime import datetime

# Şifreleme için bcrypt algoritması kullanılır
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ========== KULLANICI İŞLEMLERİ ==========

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


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not pwd_context.verify(password, user.password):
        return None
    return user


# ========== AYARLAR İŞLEMLERİ ==========

def update_or_create_settings(db: Session, user_id: int, mode: str = None, frequency: str = None, platform: str = None):
    mode = mode if mode else "duzensiz"
    platform = platform if platform else "X"
    frequency = frequency if frequency else None

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


# ========== ANALİZ İŞLEMLERİ ==========

def _content_name(content: models.ContentItem) -> str:
    """ /analysis/<name> formatından ismi çıkarır; yoksa yedek isim üretir. """
    if content.content_url:
        return content.content_url.rsplit("/", 1)[-1]
    return f"analysis_{content.id}"


def create_analysis(
    db: Session,
    user_id: int,
    analysis_name: str,
    platform: str,
    mode: str,
    frequency: str,
    data: List[schemas.CommentAnalysisItem]
):
    # 1. İçerik kaydı oluştur
    content_item = ContentItem(
        user_id=user_id,
        platform=platform,
        content_url=f"/analysis/{analysis_name}"
    )
    db.add(content_item)
    db.commit()
    db.refresh(content_item)

    # 2. Her yorum için işlem yap
    for item in data:
        # Yorum oluştur
        comment = Comment(
            content_id=content_item.id,  # FK: ContentItem.id
            text=item.comment
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        # Analiz sonucu oluştur
        has_dilekce = (
            any(label in (item.labels_hukuk or []) for label in ["a", "s", "d", "f", "g", "z", "x", "c", "v"])
            or (item.law_score is not None and item.law_score >= 0.7)
        )

        analysis_result = AnalysisResults(
            comment_id=comment.id,
            labels_hukuk=item.labels_hukuk or [],
            labels_duygu=item.labels_duygu or [],
            labels_niyet=item.labels_niyet or [],
            temizlik=item.temizlik,
            law_score=item.law_score,
            has_dilekce=has_dilekce
        )
        db.add(analysis_result)

    db.commit()
    return content_item


def get_user_analysis_results(db: Session, user_id: int) -> List[schemas.AnalysisSummary]:
    """Kullanıcının tüm analizlerini özetli şekilde getirir"""
    content_items = db.query(ContentItem).filter(ContentItem.user_id == user_id).all()

    analyses: List[schemas.AnalysisSummary] = []
    for content in content_items:
        # Bu content'e ait yorum sayısı
        total_comments = db.query(Comment).filter(Comment.content_id == content.id).count()

        # Bu content'e ait analiz edilmiş yorum sayısı
        analyzed_comments = db.query(AnalysisResults).join(Comment).filter(
            Comment.content_id == content.id
        ).count()

        # Kullanıcının ayarlarını al (mode, frequency için)
        user_settings = get_user_preferences(db, user_id)

        analysis_summary = schemas.AnalysisSummary(
            id=content.id,
            name=_content_name(content),
            date=content.created_at.strftime("%Y-%m-%d"),
            platform=content.platform,
            mode=user_settings.mode if user_settings else "duzensiz",
            frequency=user_settings.frequency if user_settings else None,
            total_comments=total_comments,
            analyzed_comments=analyzed_comments
        )
        analyses.append(analysis_summary)

    return analyses


def get_analysis_by_id(db: Session, user_id: int, analysis_id: int) -> schemas.AnalysisDetailResponse:
    """Belirli bir analizin detaylarını getirir"""
    # Content item'ı kontrol et
    content_item = db.query(ContentItem).filter(
        ContentItem.id == analysis_id,
        ContentItem.user_id == user_id
    ).first()

    if not content_item:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")

    # Bu content'e ait tüm analiz sonuçlarını getir
    analysis_results = db.query(AnalysisResults).join(Comment).filter(
        Comment.content_id == content_item.id
    ).all()

    # Summary bilgisini oluştur
    total_comments = len(analysis_results)
    user_settings = get_user_preferences(db, user_id)

    analysis_summary = schemas.AnalysisSummary(
        id=content_item.id,
        name=_content_name(content_item),
        date=content_item.created_at.strftime("%Y-%m-%d"),
        platform=content_item.platform,
        mode=user_settings.mode if user_settings else "duzensiz",
        frequency=user_settings.frequency if user_settings else None,
        total_comments=total_comments,
        analyzed_comments=total_comments
    )

    # Dağılım hesapla
    distribution = get_analysis_distribution(analysis_results)

    return schemas.AnalysisDetailResponse(
        analysis_info=analysis_summary,
        comments=analysis_results,
        distribution=distribution
    )


def filter_analysis_results(
    db: Session,
    user_id: int,
    platform: str = None,
    mode: str = None,
    frequency: str = None
) -> List[schemas.AnalysisSummary]:
    """Analizleri filtreler"""
    query = db.query(ContentItem).filter(ContentItem.user_id == user_id)

    if platform:
        query = query.filter(ContentItem.platform == platform)

    content_items = query.all()
    user_settings = get_user_preferences(db, user_id)

    # Mode ve frequency filtreleri settings tablosundan kontrol edilir
    filtered_analyses: List[schemas.AnalysisSummary] = []
    for content in content_items:
        if mode and user_settings and user_settings.mode != mode:
            continue
        if frequency and user_settings and user_settings.frequency != frequency:
            continue

        total_comments = db.query(Comment).filter(Comment.content_id == content.id).count()
        analyzed_comments = db.query(AnalysisResults).join(Comment).filter(
            Comment.content_id == content.id
        ).count()

        analysis_summary = schemas.AnalysisSummary(
            id=content.id,
            name=_content_name(content),
            date=content.created_at.strftime("%Y-%m-%d"),
            platform=content.platform,
            mode=user_settings.mode if user_settings else "duzensiz",
            frequency=user_settings.frequency if user_settings else None,
            total_comments=total_comments,
            analyzed_comments=analyzed_comments
        )
        filtered_analyses.append(analysis_summary)

    return filtered_analyses


def search_analysis_by_name(db: Session, user_id: int, query: str) -> List[schemas.AnalysisSummary]:
    """Analiz adına göre arama yapar (content_url üzerinden arar)"""
    content_items = db.query(ContentItem).filter(
        ContentItem.user_id == user_id,
        ContentItem.content_url.ilike(f"%{query}%")
    ).all()

    user_settings = get_user_preferences(db, user_id)
    analyses: List[schemas.AnalysisSummary] = []

    for content in content_items:
        total_comments = db.query(Comment).filter(Comment.content_id == content.id).count()
        analyzed_comments = db.query(AnalysisResults).join(Comment).filter(
            Comment.content_id == content.id
        ).count()

        analysis_summary = schemas.AnalysisSummary(
            id=content.id,
            name=_content_name(content),
            date=content.created_at.strftime("%Y-%m-%d"),
            platform=content.platform,
            mode=user_settings.mode if user_settings else "duzensiz",
            frequency=user_settings.frequency if user_settings else None,
            total_comments=total_comments,
            analyzed_comments=analyzed_comments
        )
        analyses.append(analysis_summary)

    return analyses


def get_dashboard_data(db: Session, user_id: int) -> schemas.DashboardResponse:
    """Dashboard için tüm verileri getirir"""
    # Kullanıcının tüm analizlerini al
    analyses = get_user_analysis_results(db, user_id)

    # Toplam istatistikleri hesapla
    total_comments = sum(analysis.total_comments for analysis in analyses)
    analyzed_comments = sum(analysis.analyzed_comments for analysis in analyses)

    # Tüm analiz sonuçlarını al (dağılım için)
    all_analysis_results = db.query(AnalysisResults).join(Comment).join(ContentItem).filter(
        ContentItem.user_id == user_id
    ).all()

    # Dağılımları hesapla
    distribution = get_analysis_distribution(all_analysis_results)

    return schemas.DashboardResponse(
        total_comments=total_comments,
        analyzed_comments=analyzed_comments,
        duygu_distribution=distribution["duygu_distribution"],
        niyet_distribution=distribution["niyet_distribution"],
        hukuki_distribution=distribution["hukuki_distribution"],
        analyses=analyses
    )


def get_analysis_distribution(analysis_results: List[AnalysisResults]) -> Dict[str, Dict[str, int]]:
    """Analiz sonuçlarından etiket dağılımını hesaplar"""
    # Tüm etiketleri topla
    all_duygu: List[str] = []
    all_niyet: List[str] = []
    all_hukuki: List[str] = []

    for result in analysis_results:
        if result.labels_duygu:
            all_duygu.extend(result.labels_duygu)
        if result.labels_niyet:
            all_niyet.extend(result.labels_niyet)
        if result.labels_hukuk:
            all_hukuki.extend(result.labels_hukuk)

    return {
        "duygu_distribution": dict(Counter(all_duygu)),
        "niyet_distribution": dict(Counter(all_niyet)),
        "hukuki_distribution": dict(Counter(all_hukuki))
    }


def get_label_distribution(db: Session, user_id: int, analysis_id: int):
    """Belirli bir analiz için etiket dağılımını getirir"""
    # analysis_id aslında content_item.id
    analysis_results = db.query(AnalysisResults).join(Comment).filter(
        Comment.content_id == analysis_id
    ).all()

    if not analysis_results:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")

    return get_analysis_distribution(analysis_results)
