from cryptography.fernet import Fernet
import base64
import hashlib

def generate_key(secret):
    return base64.urlsafe_b64encode(hashlib.sha256(secret).digest())

def encrypt_embedding(embedding, secret):
    f = Fernet(generate_key(secret))
    return f.encrypt(embedding.tobytes())

def decrypt_embedding(blob, secret):
    f = Fernet(generate_key(secret))
    return f.decrypt(blob)
