"""Transactional mail. Credentials stay server-side; never log message contents."""
import asyncio
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlsplit


def recovery_configured():
    url = urlsplit(os.environ.get('PUBLIC_APP_URL', ''))
    return bool(url.scheme == 'https' and url.netloc and not url.username and not url.query and not url.fragment
                and os.environ.get('SMTP_HOST') and os.environ.get('MAIL_FROM')
                and os.environ.get('SMTP_USERNAME') and os.environ.get('SMTP_PASSWORD'))


async def send_reset(email, token):
    message = EmailMessage()
    message['From'] = os.environ['MAIL_FROM']
    message['To'] = email
    message['Subject'] = 'Reset your RepForge password'
    link = os.environ['PUBLIC_APP_URL'].rstrip('/') + '/reset-password#token=' + token
    message.set_content(f'You requested a RepForge password reset. This link expires in 30 minutes and works once.\n\n{link}\n\nIf you did not request this, ignore this email. Your password has not changed.')

    def deliver():
        # Authenticated STARTTLS; certificate verification is always enabled.
        with smtplib.SMTP(os.environ['SMTP_HOST'], int(os.environ.get('SMTP_PORT', '587')), timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(os.environ['SMTP_USERNAME'], os.environ['SMTP_PASSWORD'])
            smtp.send_message(message)
    await asyncio.to_thread(deliver)
