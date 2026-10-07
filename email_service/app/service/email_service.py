from email.message import EmailMessage
from urllib.parse import urlencode

import aiosmtplib
from starlette.templating import Jinja2Templates

from ..repository.email_repository import EmailRepository
from ..config.config import settings

templates = Jinja2Templates(directory="app/templates")


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
        verification_url = (f"https://10.157.173.192:8443/verify_change_password?token={token}")
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


    async def send_change_status(self, client_id : str, order_number : str, order_status : str, email : str, order_items, sum : str):
        message = EmailMessage()

        message["From"] = settings.EMAIL_FROM
        message["To"] = email
        message["Subject"] = "Ваш заказ номер: " + order_number + " сменил статус"
        html = templates.get_template("email_status_order.html").render(
            client_id=client_id,
            order_number=order_number,
            order_status=order_status,
            email=email,
            order_items=order_items,
            sum=sum,
        )


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

    async def send_reset_password(self, email : str, token : str):
        message = EmailMessage()

        message["From"] = settings.EMAIL_FROM
        message["To"] = email
        message["Subject"] = "Восстановление пароля"

        params = urlencode({"token": token, "email_str": email})
        verification_url = (f"https://10.157.173.192:8443/bar_name/reset_password?{params }")
        html = f"""
                               <html>
                                   <body>
                                       <h1>Подтверждение восстановления пароля</h1>
                                       <p>
                                           Для подтверждения восстановления пароля
                                           нажмите на кнопку ниже:
                                       </p>
                                       <a href="{verification_url}">
                                           Сменить пароль
                                       </a>
                                       <p>
                                           ВНИМАНИЕ! Если вы не нажимали кнопку "Забыли пароль?", то игнорируйте это письмо и не переходите по ссылке!"
                                       </p>
                                   </body>
                               </html>
                               """
        message.set_content("Чтобы восстановить пароль - перейдите по ссылке: " + verification_url)

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