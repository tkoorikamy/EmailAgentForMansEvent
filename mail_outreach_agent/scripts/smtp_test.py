import smtplib
from email.message import EmailMessage
from getpass import getpass
import traceback


def main():
    host = input("SMTP host: ").strip()
    port = int(input("SMTP port: ").strip())
    login = input("Email/Login: ").strip()
    password = getpass("Password/App password: ")

    msg = EmailMessage()
    msg["From"] = login
    msg["To"] = login
    msg["Subject"] = "SMTP test"
    msg.set_content("Test message")

    try:
        with smtplib.SMTP_SSL(host, port, timeout=30) as s:
            s.login(login, password)
            s.send_message(msg)
        print("SUCCESS")
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()
