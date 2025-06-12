import secrets
import string
import hashlib
API_KEY_LENGTH = 32
def generate_api_key(length: int = API_KEY_LENGTH) -> str:
    """
    Generates a cryptographically secure API key.
    :param length: The length of the API key.
    :return: The API key.
    """
    secure_alphabet = string.ascii_letters + string.digits + "ñ" + "áéíúó"# salt and pepper
    return ''.join(secrets.choice(secure_alphabet) for _ in range(length))

def hash_key(key: str) -> str:
    """
    Returns a secure hash of the given API key.
    :param key: API key.
    :return: the hash of the given API key.
    """
    return hashlib.sha256(key.encode()).hexdigest()