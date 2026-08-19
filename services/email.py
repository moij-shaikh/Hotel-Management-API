import smtplib
from email.message import EmailMessage
def send_email(url,token):
    msg=EmailMessage()
    msg["From"]="sender"
    msg["To"]=url
    msg["Subject"]="Verification From Hotel API"

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login("sender_email","pass")
        smtp.send_message(msg)
        