import jwt, datetime
from config import JWT_SECRET, JWT_EXPIRY_HOURS

def generate_token(payload):
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        return None
