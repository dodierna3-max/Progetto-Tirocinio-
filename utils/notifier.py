import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailNotifier:

    def __init__(self):
        self.host      = os.getenv("SMTP_HOST", "")
        self.port      = int(os.getenv("SMTP_PORT", "587"))
        self.user      = os.getenv("SMTP_USER", "")
        self.password  = os.getenv("SMTP_PASSWORD", "")
        self.recipient = os.getenv("CLIENT_EMAIL", "")

    def send(self, subject: str, html_body: str) -> bool:
        if not self.host or not self.user or not self.password or not self.recipient:
            print("[EmailNotifier] Credenziali SMTP non configurate — invio saltato.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = self.user
        msg["To"]      = self.recipient
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, self.recipient, msg.as_string())
            return True
        except smtplib.SMTPException as e:
            print(f"[EmailNotifier] Errore SMTP: {e}")
            return False


class TelegramNotifier:

    def __init__(self):
        self.token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    def send(self, subject: str, body: str) -> bool:
        if not self.token or not self.chat_id:
            print("[TelegramNotifier] Token o Chat ID non configurati — invio saltato.")
            return False

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": f"📊 *{subject}*\n\n{body}", "parse_mode": "Markdown"},
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"[TelegramNotifier] Errore: {e}")
            return False