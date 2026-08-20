import smtplib
from email.message import EmailMessage
from config import Email_name , Email_pass

def send_email(url,token):
    msg=EmailMessage()
    msg["From"]=Email_name
    msg["To"]=url
    msg["Subject"]="Verification From Hotel API"
    msg.add_alternative(f"""
<a href='http://127.0.0.1:8000/user/auth/verify?token={token}'>Click </a>
""",subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(Email_name,Email_pass)
        smtp.send_message(msg)
        