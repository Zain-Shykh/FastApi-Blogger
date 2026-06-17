from email.message import EmailMessage
import aiosmtplib
from fastapi.templating import Jinja2Templates
from config import settings


templates = Jinja2Templates(directory="templates")

async def send_email(to_email:str, subject:str, plain_text:str, html_content:str | None = None)->None:
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(plain_text)

    if html_content:
        message.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.mail_server,
        port=settings.mail_port,
        username=settings.mail_username,
        password=settings.mail_password.get_secret_value(),
        use_tls=settings.mail_use_tls
    )

async def send_password_reset_email(to_email:str, username:str, token:str)->None:
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    template = templates.env.get_template("password_reset_email.html")
    html_content = template.render(username=username, reset_url=reset_url)

    plain_text = f"""HI {username},
You requested a password reset. Please click the link below to reset your password:
{reset_url}
If you did not request this, please ignore this email.
link will expire in {settings.reset_token_expire_minutes} minutes.
Best regards,
The FastAPI Blog Team
"""
    
    await send_email(to_email, "Password Reset Request", plain_text, html_content)