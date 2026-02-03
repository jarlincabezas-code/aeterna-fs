import hashlib
import hmac
import os

HASH_ALGO = hashlib.sha3_512

SECRET_KEY = os.environ.get(
    "AETERNA_KEY",
    b"NIST_800_86_PLATINUM_2026_PRO_SECURE_TOKEN"
)

def generate_hash(data: str) -> str:
    """Deterministic SHA3-512 hash."""
    return HASH_ALGO(data.encode("utf-8")).hexdigest()

def sign_data(data_hash: str) -> str:
    """
    Cryptographic authentication using HMAC-SHA3-512.
    Verification restricted to authorized Aeterna systems.
    """
    key = SECRET_KEY.encode() if isinstance(SECRET_KEY, str) else SECRET_KEY
    return hmac.new(key, data_hash.encode(), HASH_ALGO).hexdigest()
