from email.message import EmailMessage

import aiosmtplib

from ..repository.email_repository import EmailRepository
from ..config.config import settings


class EmailService:

    def __init__(self, email_repository : EmailRepository):
        self.email_repository = email_repository

    async def send_verification_email(self, email : str, token : str):
        message = EmailMessage()

        message["From"] = settings.EMAIL_FROM
        message["To"] = email
        message["Subject"] = "Подтверждение email"
        verification_url = (f"http://localhost:8080/verify_email?token={token}")

        html = f"""
                <html>
                    <body>
                        <h1>Подтверждение email</h1>
                        <p>
                            Для подтверждения вашего email
                            нажмите на кнопку ниже:
                        </p>
                        <a href="{verification_url}">
                            Подтвердить email
                        </a>
                    </body>
                </html>
                """

        message.set_content("Для подтверждения email перейдите по ссылке: "+verification_url)
        message.add_alternative(html, subtype="html",)
        await aiosmtplib.send(
            message,
            hostname=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_USERNAME,
            password=settings.EMAIL_PASSWORD,
            start_tls=True,
        )
