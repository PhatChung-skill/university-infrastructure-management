import hashlib
import secrets
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


def generate_six_digit_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def hash_reset_code(email: str, code: str) -> str:
    payload = f"{settings.SECRET_KEY}:{email.strip().lower()}:{code}"
    return hashlib.sha256(payload.encode()).hexdigest()


def send_password_reset_code_email(*, to_email: str, code: str, request) -> None:
    subject = getattr(
        settings,
        "PASSWORD_RESET_EMAIL_SUBJECT",
        "[HCMUNRE] Mã xác nhận đặt lại mật khẩu",
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost")
    ctx = {
        "code": code,
        "to_email": to_email,
        "brand_name": getattr(settings, "PASSWORD_RESET_EMAIL_BRAND", "HCMUNRE IT"),
        "support_line": getattr(settings, "PASSWORD_RESET_SUPPORT_LINE", ""),
    }
    text_body = render_to_string("auth/emails/password_reset_code.txt", ctx, request=request)
    html_body = render_to_string("auth/emails/password_reset_code.html", ctx, request=request)
    msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
