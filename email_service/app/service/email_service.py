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
        smtp = aiosmtplib.SMTP(
            hostname=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            timeout=20,
        )

        await smtp.connect()
        await smtp.login(
            settings.EMAIL_USERNAME,
            settings.EMAIL_PASSWORD,
        )
        await smtp.send_message(message)
        await smtp.quit()

    async def send_change_password_verification(self, email : str, token : str):
        message = EmailMessage()

        message["From"] = settings.EMAIL_FROM
        message["To"] = email
        message["Subject"] = "Подтверждение email"
        verification_url = (f"http://localhost:8080/verify_change_password?token={token}")
        html = f"""
                        <html>
                            <body>
                                <h1>Подтверждение смены пароля</h1>
                                <p>
                                    Для подтверждения смены пароля
                                    нажмите на кнопку ниже:
                                </p>
                                <a href="{verification_url}">
                                    Сменить пароль
                                </a>
                            </body>
                        </html>
                        """
        message.set_content("Для подтверждения email перейдите по ссылке: " + verification_url)
        message.add_alternative(html, subtype="html", )
        smtp = aiosmtplib.SMTP(
            hostname=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            timeout=20,
        )

        await smtp.connect()
        await smtp.login(
            settings.EMAIL_USERNAME,
            settings.EMAIL_PASSWORD,
        )
        await smtp.send_message(message)
        await smtp.quit()

