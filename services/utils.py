import secrets

def generate_email_token()->str:
    return str(secrets.token_urlsafe(32))