from jobs import send_email ,send_password_otp

class WorkerSettings:
    functions=[send_email,send_password_otp]
    job_timeout=60