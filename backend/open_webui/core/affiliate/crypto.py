import json
import os
from typing import Any

from cryptography.fernet import Fernet

# Environment variable holding base64 encoded key
_KEY_ENV = "AFFILIATE_PAYOUT_ENCRYPTION_KEY"
_key = os.environ.get(_KEY_ENV)
if not _key:
    # Generate ephemeral key if none provided
    _key = Fernet.generate_key().decode()
fernet = Fernet(_key.encode() if isinstance(_key, str) else _key)


def encrypt_details(details: Any) -> str:
    """Encrypt payout details dictionary to a string."""
    data = json.dumps(details).encode()
    return fernet.encrypt(data).decode()


def decrypt_details(token: str) -> Any:
    """Decrypt payout details string back to dictionary."""
    data = fernet.decrypt(token.encode()).decode()
    return json.loads(data)
