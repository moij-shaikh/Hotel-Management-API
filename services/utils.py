import secrets
from pwdlib import PasswordHash


def generate_email_token()->str:
    return str(secrets.token_urlsafe(32))
def generate_otp()->str:
    return str(secrets.token_urlsafe(4))
pass_hasher=PasswordHash.recommended()