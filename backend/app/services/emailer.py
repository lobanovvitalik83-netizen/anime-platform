import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_reset_email(to_email: str, reset_url: str) -> None:
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.smtp_from_email]):
        raise RuntimeError("SMTP is not configured")
    msg = EmailMessage()
    msg["Subject"] = "Password reset"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email
    msg.set_content(f"Use this link to reset your password: {reset_url}")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
