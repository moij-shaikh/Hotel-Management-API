import secrets

def generate_email_token():
    return secrets.token_urlsafe(32)