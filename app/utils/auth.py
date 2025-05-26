import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, SecurityScopes
from typing import Optional

from app.config import Config
from app.utils.exceptions import NumerusXBaseError # Assuming you have custom exceptions

class AuthError(NumerusXBaseError):
    def __init__(self, error_detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(error_detail)
        self.error_detail = error_detail
        self.status_code = status_code

class MissingTokenAuthError(AuthError):
    def __init__(self):
        super().__init__("Requires authentication", status.HTTP_401_UNAUTHORIZED)

class InvalidTokenAuthError(AuthError):
    def __init__(self, detail: str):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)

# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()

class VerifyToken:
    """Does all the token verification using PyJWT."""
    def __init__(self):
        self.jwks_uri = Config.AUTH_PROVIDER_JWKS_URI
        self.audience = Config.AUTH_PROVIDER_AUDIENCE
        self.issuer = Config.AUTH_PROVIDER_ISSUER
        self.algorithms = [Config.AUTH_PROVIDER_ALGORITHMS]

        if not all([self.jwks_uri, self.audience, self.issuer]):
            # This is a server configuration error, should ideally prevent startup
            raise RuntimeError(
                "Auth provider JWKS URI, Audience, or Issuer not configured. "
                "Please set AUTH_PROVIDER_JWKS_URI, AUTH_PROVIDER_AUDIENCE, and AUTH_PROVIDER_ISSUER."
            )
        
        self.jwks_client = jwt.PyJWKClient(self.jwks_uri)

    async def verify(self,
                     security_scopes: SecurityScopes, # FastAPI uses this for OAuth2 scopes, can be ignored if not using scopes
                     token: Optional[HTTPAuthorizationCredentials] = Depends(token_auth_scheme)
                     ):
        if token is None:
            raise MissingTokenAuthError()
        
        unverified_token_credentials = token.credentials

        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(
                unverified_token_credentials
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            raise InvalidTokenAuthError(f"Error fetching signing key: {error}")
        except jwt.exceptions.DecodeError as error:
            raise InvalidTokenAuthError(f"Token decoding error (kid): {error}")
        except Exception as e: # Catch any other unexpected errors during key fetching
            raise InvalidTokenAuthError(f"Unexpected error getting signing key: {e}")

        try:
            payload = jwt.decode(
                unverified_token_credentials,
                signing_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
            )
        except jwt.ExpiredSignatureError as error:
            raise InvalidTokenAuthError(f"Token is expired: {error}")
        except jwt.InvalidAudienceError as error:
            raise InvalidTokenAuthError(f"Invalid token audience: {error}")
        except jwt.InvalidIssuerError as error:
            raise InvalidTokenAuthError(f"Invalid token issuer: {error}")
        except jwt.InvalidTokenError as error: # Generic PyJWT error
            raise InvalidTokenAuthError(f"Invalid token: {error}")
        except Exception as error: # Catch any other unexpected JWT errors
            raise InvalidTokenAuthError(f"Unexpected error decoding token: {error}")
        
        # Here you could add permission checking if permissions are part of the JWT payload
        # For example:
        # if security_scopes.scopes: # If scopes are defined for the endpoint
        #     token_scopes = payload.get("scp", "") # Or however scopes are named in your token
        #     if isinstance(token_scopes, str):
        #         token_scopes_list = token_scopes.split()
        #     elif isinstance(token_scopes, list):
        #         token_scopes_list = token_scopes
        #     else:
        #         token_scopes_list = []
            
        #     for scope in security_scopes.scopes:
        #         if scope not in token_scopes_list:
        #             raise InvalidTokenAuthError(
        #                 f"Missing required scope: {scope}. Token has scopes: {token_scopes_list}"
        #             )

        return payload # Contains decoded JWT claims 