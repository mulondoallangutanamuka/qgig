import os
from datetime import datetime, timedelta

import bcrypt

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.job import Job, JobStatus


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _get_or_create_user(db, email: str, password: str, role: UserRole, username: str | None = None) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Ensure role is correct
        if user.role != role:
            user.role = role
        return user

    user = User(
        email=email,
        username=username,
        password=_hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _ensure_profiles(db, user: User) -> None:
    prof = db.query(Professional).filter(Professional.user_id == user.id).first()
    if not prof:
        db.add(Professional(user_id=user.id))

    inst = db.query(Institution).filter(Institution.user_id == user.id).first()
    if not inst:
        db.add(Institution(user_id=user.id))


def seed() -> None:
    # Ensure tables exist (first deploy convenience; migrations are better long-term)
    Base.metadata.create_all(bind=engine)

    admin_email = os.getenv("ADMIN_EMAIL", "admin@qgig.local")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")

    institution_email = os.getenv("SEED_INSTITUTION_EMAIL", "institution@qgig.local")
    institution_password = os.getenv("SEED_INSTITUTION_PASSWORD", "Institution123!")

    professional_email = os.getenv("SEED_PROFESSIONAL_EMAIL", "professional@qgig.local")
    professional_password = os.getenv("SEED_PROFESSIONAL_PASSWORD", "Professional123!")

    db = SessionLocal()
    try:
        admin = _get_or_create_user(db, admin_email, admin_password, UserRole.ADMIN, username="admin")
        _ensure_profiles(db, admin)

        institution_user = _get_or_create_user(
            db,
            institution_email,
            institution_password,
            UserRole.INSTITUTION,
            username="institution",
        )
        _ensure_profiles(db, institution_user)

        professional_user = _get_or_create_user(
            db,
            professional_email,
            professional_password,
            UserRole.PROFESSIONAL,
            username="professional",
        )
        _ensure_profiles(db, professional_user)

        db.flush()

        institution = db.query(Institution).filter(Institution.user_id == institution_user.id).first()
        if institution:
            if not institution.institution_name:
                institution.institution_name = "QGig Demo Hospital"
            if not institution.location:
                institution.location = "Kampala"
            if not institution.contact_email:
                institution.contact_email = institution_email

        professional = db.query(Professional).filter(Professional.user_id == professional_user.id).first()
        if professional:
            if not professional.full_name:
                professional.full_name = "Demo Professional"
            if not professional.location:
                professional.location = "Kampala"
            if not professional.profession_category:
                professional.profession_category = "Healthcare"
            if not professional.skills:
                professional.skills = "Patient care, triage, teamwork"

        db.flush()

        # Seed a few jobs (idempotent by title)
        if institution:
            existing_titles = {
                title
                for (title,) in db.query(Job.title)
                .filter(Job.institution_id == institution.id)
                .all()
            }

            sample_jobs = [
                {
                    "title": "Night Shift Nurse (1 night)",
                    "description": "Cover a single night shift in the general ward.",
                    "location": "Kampala",
                    "pay_amount": 150000,
                    "duration_hours": 10,
                    "is_urgent": True,
                    "start_date": datetime.utcnow() + timedelta(days=1),
                    "job_type": "Nursing",
                    "sector": "Healthcare",
                },
                {
                    "title": "Lab Assistant (Weekend)",
                    "description": "Assist with sample collection and labeling over the weekend.",
                    "location": "Kampala",
                    "pay_amount": 120000,
                    "duration_hours": 8,
                    "is_urgent": False,
                    "start_date": datetime.utcnow() + timedelta(days=3),
                    "job_type": "Laboratory",
                    "sector": "Healthcare",
                },
                {
                    "title": "Physio Support (Half-day)",
                    "description": "Support physiotherapy sessions and patient guidance.",
                    "location": "Wakiso",
                    "pay_amount": 80000,
                    "duration_hours": 4,
                    "is_urgent": False,
                    "start_date": datetime.utcnow() + timedelta(days=5),
                    "job_type": "Physiotherapy",
                    "sector": "Healthcare",
                },
            ]

            for payload in sample_jobs:
                if payload["title"] in existing_titles:
                    continue
                db.add(
                    Job(
                        institution_id=institution.id,
                        title=payload["title"],
                        description=payload["description"],
                        location=payload["location"],
                        pay_amount=float(payload["pay_amount"]),
                        duration_hours=float(payload["duration_hours"]),
                        is_urgent=bool(payload["is_urgent"]),
                        status=JobStatus.OPEN,
                        start_date=payload["start_date"],
                        job_type=payload["job_type"],
                        sector=payload["sector"],
                    )
                )

        db.commit()

        print("Seed complete")
        print(f"Admin: {admin_email} / {admin_password}")
        print(f"Institution: {institution_email} / {institution_password}")
        print(f"Professional: {professional_email} / {professional_password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
