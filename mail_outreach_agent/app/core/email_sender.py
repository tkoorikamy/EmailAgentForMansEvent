import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path


def build_message(sender_email: str, sender_name: str, recipient: str, subject: str, body: str, attachment_path: str | None = None) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        p = Path(attachment_path)
        ctype, _ = mimetypes.guess_type(str(p))
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)
    return msg


def send_email(settings: dict, password: str, message: EmailMessage) -> tuple[bool, str]:
    host = settings["smtp_host"]
    port = int(settings["smtp_port"])
    try:
        if settings.get("smtp_ssl", True):
            with smtplib.SMTP_SSL(host, port, timeout=20) as server:
                server.login(settings["smtp_login"], password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                if settings.get("smtp_starttls", False):
                    server.starttls()
                server.login(settings["smtp_login"], password)
                server.send_message(message)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
