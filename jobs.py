def generate_bill_pdf():
    from fpdf import FPDF

    f = FPDF()
    f.add_page()

    f.set_font("helvetica", size=24, style="BI")
    f.cell(0, 24, "Hotel API Bill", align="C", border="B")

    f.ln(24)

    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Guest Name:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "John Doe", ln=True)

    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Booking ID:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "123", ln=True)

    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Booking Date:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "25 Aug 2026", ln=True)

    f.ln(5)


    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Room No:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "20", ln=True)

    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Room Type:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "Suite", ln=True)

    f.ln(5)



    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Check-in:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "25 Aug 2026", ln=True)

    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Check-out:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "28 Aug 2026", ln=True)

    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Total Days:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "3", ln=True)

    f.ln(5)


    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Total Price:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "Rs. 6000", ln=True)

    f.set_font("helvetica", size=16, style="BI")
    f.cell(50, 10, "Status:")

    f.set_font("helvetica", size=16)
    f.cell(0, 10, "RESERVED", ln=True)

    f.ln(15)


    f.set_font("helvetica", size=12, style="I")
    f.cell(0, 10, "Thank you for choosing our hotel!", align="C")

    f.output("invoice.pdf")

async def send_email(ctx,email,token):
    import smtplib
    from email.message import EmailMessage
    from config import Email_name , Email_pass
    msg=EmailMessage()
    msg["From"]=Email_name
    msg["To"]=email
    msg["Subject"]="Verification From Hotel API"
    msg.add_alternative(f"""
    <a href='http://127.0.0.1:8000/user/auth/verify?token={token}'>Click </a>
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
    with smtplib.SMTP_SSL("smtp.google.com",465) as smtp:
        smtp.login(Email_name,Email_pass)
        smtp.send_message(msg)