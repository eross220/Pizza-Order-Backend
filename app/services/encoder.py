from enum import StrEnum

from passlib.context import CryptContext


hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenType(StrEnum):
    ACTIVATION = "ACTIVATION"
    AUTHENTICATION = "AUTHENTICATION"
    REFRESH = "REFRESH"
    PASSWORD_RESET = "PASSWORD_RESET"


def hash_secret(secret: str) -> str:
    """Hashes a secret using passlib
    :param secret: Plain text secret.
    :type secret: str
    :return: Hashed secret.
    :rtype: str
    """
    return hasher.hash(secret)

def is_valid_secret(hashed_secret: str, secret: str):
    """Verifies a secret against a hashed secret.
    :param hashed_secret: Hashed secret.
    :type hashed_secret: str
    :param secret: Plain text secret.
    :type secret: str
    :return: True if secret is valid, False otherwise.
    :rtype: bool
    """
    return hasher.verify(secret, hashed_secret)

