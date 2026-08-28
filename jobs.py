
async def send_email(ctx,email,token):
    import smtplib
    from email.message import EmailMessage
    from config import Email_name , Email_pass
    msg=EmailMessage()
    msg["From"]=Email_name
    msg["To"]=email
    msg["Subject"]="Verification From Hotel API"
    msg.add_alternative(f"""
    <a href='http://127.0.0.1:8000/user/auth/verify-email?token={token}'>Click </a>
    """,subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(Email_name,Email_pass)
        smtp.send_message(msg)

async def send_password_otp(ctx,email,otp):
    import smtplib
    from email.message import EmailMessage
    from config import Email_name , Email_pass
    msg=EmailMessage()
    msg["From"]=Email_name
    msg["To"]=email
    msg["Subject"]="Hotel API OTP"
    msg.set_content(f"If you have not requested this opt, Please secure your account someone else made have access.\n OTP: {otp}")
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(Email_name,Email_pass)
        smtp.send_message(msg)