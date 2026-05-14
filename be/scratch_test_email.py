import asyncio
from app.services.email.email_service import get_email_service
from app.core.config import settings

async def test_email_sending():
    print("--- Checking Email Config ---")
    print(f"Host: {settings.SMTP_HOST}")
    print(f"Port: {settings.SMTP_PORT}")
    print(f"User: {settings.SMTP_USER}")
    print(f"From: {settings.SMTP_FROM_EMAIL}")
    print(f"TLS Enabled: {settings.SMTP_USE_TLS}")
    print(f"Send Enabled: {settings.EMAIL_SENDING_ENABLED}")
    
    service = get_email_service()
    
    test_email = "buinhathuy263@gmail.com" # User's own email from env
    print(f"\nAttempting to send test OTP to: {test_email}")
    
    try:
        # Intentionally override enabled flag just in case
        settings.EMAIL_SENDING_ENABLED = True
        await service.send_otp_email(test_email, "123456")
        print("✅ SUCCESS! Email sent successfully.")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_sending())
