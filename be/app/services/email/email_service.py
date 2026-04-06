import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.exceptions import BadRequestException


class EmailService:
    """Simple SMTP email sender for OTP delivery."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_from: str,
        use_tls: bool,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.use_tls = use_tls

    async def send_otp_email(self, to_email: str, otp: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Your verification OTP"
        message["From"] = self.smtp_from
        message["To"] = to_email
        message.set_content(
            (
                "Your OTP code is: "
                f"{otp}\n\n"
                "This code expires in 5 minutes.\n"
                "If you did not request this, please ignore this email."
            )
        )

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.smtp_user and self.smtp_password:
                    smtp.login(self.smtp_user, self.smtp_password)
                smtp.send_message(message)
        except Exception as exc:
            raise BadRequestException("Failed to send OTP email") from exc



def get_email_service() -> EmailService:
    return EmailService(
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_password=settings.SMTP_PASSWORD,
        smtp_from=settings.SMTP_FROM_EMAIL,
        use_tls=settings.SMTP_USE_TLS,
    )
