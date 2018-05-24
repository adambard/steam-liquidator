from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

import base64

BACKEND = default_backend()


def make_key(mod, exp):
    return RSAPublicNumbers(exp, mod).public_key(BACKEND)


def encrypt(key, message):
    return base64.b64encode(key.encrypt(message.encode('utf-8'), PKCS1v15())).decode('utf-8')
