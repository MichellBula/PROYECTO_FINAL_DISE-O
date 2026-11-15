from functools import lru_cache

import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

from config import config

bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def jwks():
    return PyJWKClient(
        f"https://login.microsoftonline.com/{config.ENTRA_TENANT_ID}/discovery/v2.0/keys",
        timeout=5,
    )


def usuario_autenticado(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Security(bearer),
) -> dict:
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Falta token de acceso")

    try:
        clave = jwks().get_signing_key_from_jwt(credenciales.credentials)
        claims = jwt.decode(
            credenciales.credentials,
            clave.key,
            algorithms=["RS256"],
            audience=config.ENTRA_API_CLIENT_ID,
            issuer=f"https://login.microsoftonline.com/{config.ENTRA_TENANT_ID}/v2.0",
            options={"require": ["exp", "iat", "iss", "aud", "tid", "ver", "oid"]},
            leeway=30,
        )
    except PyJWKClientConnectionError as exc:
        raise HTTPException(status_code=503, detail="Validación de identidad no disponible") from exc
    except (jwt.InvalidTokenError, PyJWKClientError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Token de acceso inválido") from exc
    except Exception as exc:
        # Por ejemplo, no se puede obtener la clave de firma por falta de red.
        raise HTTPException(status_code=503, detail="Validación de identidad no disponible") from exc

    if claims.get("ver") != "2.0" or claims.get("tid", "").lower() != config.ENTRA_TENANT_ID.lower():
        raise HTTPException(status_code=401, detail="Emisor de token no admitido")

    scopes = set(str(claims.get("scp", "")).split())
    if config.ENTRA_REQUIRED_SCOPE not in scopes:
        raise HTTPException(status_code=403, detail="No tiene el permiso requerido")

    # oid identifica de forma estable al usuario dentro del tenant.
    request.state.usuario_auditoria = f"{claims['tid']}:{claims['oid']}"
    return claims
