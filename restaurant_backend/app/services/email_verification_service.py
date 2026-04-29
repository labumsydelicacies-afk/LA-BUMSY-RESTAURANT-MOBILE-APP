#==============================#
#   EMAIL VERIFICATION SERVICE #
#==============================#

import hashlib
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.config import SMTP_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT
from app.db.models import EmailVerification, User


OTP_EXPIRY_MINUTES = 10


def get_latest_unused_otp(session: Session, user_id: int) -> EmailVerification | None:
    return (
        session.query(EmailVerification)
        .filter(
            EmailVerification.user_id == user_id,
            EmailVerification.is_used.is_(False),
        )
        .order_by(EmailVerification.created_at.desc())
        .first()
    )


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def hash_otp(otp: str) -> str:
    """Hash OTP before storing in the database."""
    return hashlib.sha256(otp.encode()).hexdigest()


def create_otp(session: Session, user_id: int) -> str:
    otp = generate_otp()
    otp_hash = hash_otp(otp)

    record = EmailVerification(
        user_id=user_id,
        code_hash=otp_hash,
        expires_at=datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        is_used=False,
        created_at=datetime.now(),
    )

    session.add(record)
    session.commit()
    session.refresh(record)

    return otp


def send_email(to_email: str, subject: str, body: str) -> None:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise ValueError("SMTP_EMAIL and SMTP_PASSWORD must be set")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)


def send_verification_email(session: Session, user: User) -> None:
    otp = create_otp(session, user.id)
    send_email(
        to_email=user.email,
        subject="Your verification code",
        body=f"Your verification code is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
    )


def verify_otp_for_user(session: Session, user_id: int, otp: str) -> bool:
    record = get_latest_unused_otp(session, user_id)
    if not record:
        return False

    if record.expires_at < datetime.now():
        return False

    if record.code_hash != hash_otp(otp):
        return False

    user = session.query(User).filter(User.id == user_id).first()
    if user is None:
        return False

    record.is_used = True
    user.is_verified = True
    session.commit()
    return True
