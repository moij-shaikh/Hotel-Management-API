import secrets
from pwdlib import PasswordHash


def generate_email_token()->str:
    return str(secrets.token_urlsafe(32))

pass_hasher=PasswordHash.recommended()