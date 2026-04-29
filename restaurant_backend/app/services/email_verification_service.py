#==============================#
#   EMAIL VERIFICATION SERVICE #
#==============================#

import hashlib
import logging
import random
import ssl
import smtplib
import time
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import SMTP_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT
from app.db.models import EmailVerification, User

logger = logging.getLogger(__name__)


OTP_EXPIRY_MINUTES = 10
SMTP_TIMEOUT_SECONDS = 10
SMTP_SSL_CONTEXT = ssl.create_default_context()


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

    # Invalidate any previously unused OTPs so only the latest one is valid.
    session.query(EmailVerification).filter(
        EmailVerification.user_id == user_id,
        EmailVerification.is_used.is_(False),
    ).update({EmailVerification.is_used: True}, synchronize_session=False)

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
    logger.info("OTP created for user_id=%s", user_id)

    return otp


def send_email(to_email: str, subject: str, body: str) -> None:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise ValueError("SMTP_EMAIL and SMTP_PASSWORD must be set")

    normalized_subject = subject.strip() or "Email verification"

    msg = EmailMessage()
    msg["Subject"] = normalized_subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL(
        SMTP_HOST,
        SMTP_PORT,
        timeout=SMTP_TIMEOUT_SECONDS,
        context=SMTP_SSL_CONTEXT,
    ) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)


def send_verification_email(session: Session, user: User) -> None:
    otp = create_otp(session, user.id)
    send_email(
        to_email=user.email,
        subject="Your verification code",
        body=f"Your verification code is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
    )


def send_verification_email_async(to_email: str, otp: str) -> None:
    """
    Send OTP email outside request lifecycle.
    SMTP failures are logged but should not invalidate registration.
    """
    # Precompute static content before opening the SMTP connection.
    subject = "Your verification code"
    body = f"Your verification code is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes."

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.error("Verification email skipped for %s: SMTP credentials are missing", to_email)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(body)

    started = time.perf_counter()
    try:
        before_connect = time.perf_counter()
        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            timeout=SMTP_TIMEOUT_SECONDS,
            context=SMTP_SSL_CONTEXT,
        ) as server:
            connected_at = time.perf_counter()
            logger.info(
                "SMTP connected for %s in %.3fs",
                to_email,
                connected_at - before_connect,
            )
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            logged_in_at = time.perf_counter()
            logger.info(
                "SMTP login completed for %s in %.3fs",
                to_email,
                logged_in_at - connected_at,
            )
            server.send_message(msg)
            sent_at = time.perf_counter()
            logger.info(
                "SMTP send completed for %s in %.3fs",
                to_email,
                sent_at - logged_in_at,
            )

        total = time.perf_counter() - started
        logger.info("Verification email sent successfully to %s (total %.3fs)", to_email, total)
    except Exception:
        total = time.perf_counter() - started
        logger.exception("Failed to send verification email to %s after %.3fs", to_email, total)


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
