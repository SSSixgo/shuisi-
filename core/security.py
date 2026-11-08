import hashlib, hmac, secrets, base64, socket, os
try: 
    import win32crypt
    HAS_DPAPI = True
except: 
    HAS_DPAPI = False
try: 
    from cryptography.fernet import Fernet
    HAS_FERNET = True
except: 
    HAS_FERNET = False
from core.config import PBKDF2_ITERATIONS

def hash_pwd(pwd, salt=None, iterations=PBKDF2_ITERATIONS):
    salt_bytes = salt or secrets.token_bytes(16)
    if isinstance(salt_bytes, str): salt_bytes = bytes.fromhex(salt_bytes)
    digest = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt_bytes, iterations)
    return f"pbkdf2_sha256${iterations}${salt_bytes.hex()}${digest.hex()}"

def verify_pwd(pwd, stored):
    if not stored: return False
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt_hex, expected = stored.split("$", 3)
            actual = hash_pwd(pwd, bytes.fromhex(salt_hex), int(rounds)).split("$", 3)[3]
            return hmac.compare_digest(actual, expected)
        except Exception: return False
    return hmac.compare_digest(hashlib.sha256(pwd.encode("utf-8")).hexdigest(), stored)

def _machine_key():
    seed = f"{socket.gethostname()}|{os.getlogin() if hasattr(os, 'getlogin') else 'user'}"
    return base64.urlsafe_b64encode(hashlib.sha256(seed.encode()).digest())

def _protect_secret(secret):
    if HAS_DPAPI:
        try:
            blob = win32crypt.CryptProtectData(secret.encode("utf-8"), "shuisi_remember", None, None, None, 0)
            return "dpapi:" + base64.b64encode(blob).decode()
        except Exception: pass
    if HAS_FERNET:
        try: return "fernet:" + Fernet(_machine_key()).encrypt(secret.encode()).decode()
        except Exception: pass
    return secret

def _unprotect_secret(token):
    if token.startswith("dpapi:"):
        if not HAS_DPAPI: raise RuntimeError("DPAPI 不可用")
        return win32crypt.CryptUnprotectData(base64.b64decode(token[6:]), None, None, None, 0)[1].decode()
    if token.startswith("fernet:"):
        if not HAS_FERNET: raise RuntimeError("Fernet 不可用")
        return Fernet(_machine_key()).decrypt(token[7:].encode()).decode()
    return token