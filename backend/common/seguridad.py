"""Contraseñas y tokens de sesión. Solo usa la biblioteca estándar de Python.

Contraseñas: se guardan con scrypt (función lenta a propósito, con sal aleatoria).
  Formato del hash: scrypt$n$r$p$sal_base64$hash_base64

Tokens: JWT firmado con HS256 (estándar, se puede revisar en jwt.io).
  La llave de firma se lee de Secrets Manager (TOKEN_SECRET_NAME) en AWS,
  o de TOKEN_SECRET en el .env en local. Nunca va en el código.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import string
import time

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1
SCRYPT_MEMORIA = 64 * 1024 * 1024
HORAS_SESION = 8

_llave_token = None


# ---------- Contraseñas ----------

def _scrypt(contrasena, sal, n, r, p):
    return hashlib.scrypt(
        contrasena.encode("utf-8"), salt=sal, n=n, r=r, p=p, maxmem=SCRYPT_MEMORIA, dklen=32
    )


def cifrar_contrasena(contrasena):
    sal = secrets.token_bytes(16)
    resumen = _scrypt(contrasena, sal, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return "$".join(
        [
            "scrypt",
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            base64.b64encode(sal).decode(),
            base64.b64encode(resumen).decode(),
        ]
    )


def verificar_contrasena(contrasena, hash_guardado):
    try:
        algoritmo, n, r, p, sal, resumen = hash_guardado.split("$")
        if algoritmo != "scrypt":
            return False
        calculado = _scrypt(contrasena, base64.b64decode(sal), int(n), int(r), int(p))
    except (ValueError, TypeError, AttributeError):
        return False
    return hmac.compare_digest(calculado, base64.b64decode(resumen))


# Hash de relleno: cuando el correo no existe se verifica contra este hash, para que la
# respuesta tarde lo mismo y no se pueda adivinar qué correos están registrados.
HASH_RELLENO = cifrar_contrasena(secrets.token_urlsafe(16))


def validar_contrasena_nueva(contrasena):
    """Regresa None si es válida, o el mensaje del problema."""
    if not isinstance(contrasena, str) or not 8 <= len(contrasena) <= 72:
        return "La contraseña debe tener de 8 a 72 caracteres."
    if not any(c.isalpha() for c in contrasena) or not any(c.isdigit() for c in contrasena):
        return "La contraseña debe tener al menos una letra y un número."
    return None


def generar_contrasena_temporal(largo=10):
    """Contraseña aleatoria fácil de dictar (sin letras que se confunden como l, 1, O, 0)."""
    letras = "".join(c for c in string.ascii_letters + string.digits if c not in "lI1O0o")
    while True:
        contrasena = "".join(secrets.choice(letras) for _ in range(largo))
        if validar_contrasena_nueva(contrasena) is None:
            return contrasena


# ---------- Tokens (JWT HS256) ----------

def _b64url(datos):
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _b64url_decodificar(texto):
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _llave():
    global _llave_token
    if _llave_token is None:
        nombre_secreto = os.environ.get("TOKEN_SECRET_NAME")
        if nombre_secreto:
            import boto3

            cliente = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION"))
            valor = cliente.get_secret_value(SecretId=nombre_secreto)["SecretString"]
        else:
            valor = os.environ.get("TOKEN_SECRET", "")
        if len(valor) < 32:
            raise RuntimeError("La llave de los tokens debe tener al menos 32 caracteres.")
        _llave_token = valor.encode("utf-8")
    return _llave_token


def crear_token(datos, horas=HORAS_SESION, ahora=None):
    ahora = int(ahora if ahora is not None else time.time())
    encabezado = {"alg": "HS256", "typ": "JWT"}
    cuerpo = {**datos, "iat": ahora, "exp": ahora + horas * 3600}
    partes = [
        _b64url(json.dumps(encabezado, separators=(",", ":")).encode()),
        _b64url(json.dumps(cuerpo, separators=(",", ":")).encode()),
    ]
    firma = hmac.new(_llave(), ".".join(partes).encode(), hashlib.sha256).digest()
    return ".".join(partes + [_b64url(firma)])


def verificar_token(token, ahora=None):
    """Regresa el contenido del token si es válido y no ha caducado; si no, None."""
    if not isinstance(token, str) or token.count(".") != 2:
        return None
    encabezado, cuerpo, firma = token.split(".")
    esperada = hmac.new(_llave(), f"{encabezado}.{cuerpo}".encode(), hashlib.sha256).digest()
    try:
        if not hmac.compare_digest(esperada, _b64url_decodificar(firma)):
            return None
        if json.loads(_b64url_decodificar(encabezado)).get("alg") != "HS256":
            return None
        datos = json.loads(_b64url_decodificar(cuerpo))
    except ValueError:
        return None
    ahora = ahora if ahora is not None else time.time()
    if not isinstance(datos, dict) or datos.get("exp", 0) <= ahora:
        return None
    return datos


def leer_token(evento):
    """Saca y verifica el token del encabezado Authorization: Bearer <token>."""
    encabezados = {k.lower(): v for k, v in (evento.get("headers") or {}).items()}
    valor = encabezados.get("authorization") or ""
    if not valor.lower().startswith("bearer "):
        return None
    return verificar_token(valor[7:].strip())
