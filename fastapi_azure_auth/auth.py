import inspect
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional

import jwt
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from fastapi.security.base import SecurityBase
from jwt.exceptions import (
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAudienceError,
    InvalidIssuedAtError,
    InvalidIssuerError,
    InvalidTokenError,
    MissingRequiredClaimError,
)
from starlette.requests import HTTPConnection

from fastapi_azure_auth.exceptions import (
    Forbidden,
    ForbiddenHttp,
    ForbiddenWebSocket,
    InvalidAuthHttp,
    InvalidAuthWebSocket,
    InvalidRequest,
    InvalidRequestHttp,
    Unauthorized,
    UnauthorizedHttp,
    UnauthorizedWebSocket,
)
from fastapi_azure_auth.openid_config import OpenIdConfig
from fastapi_azure_auth.user import User
from fastapi_azure_auth.utils import get_unverified_claims, get_unverified_header, is_guest

if TYPE_CHECKING:  # pragma: no cover
    from jwt.algorithms import AllowedPublicKeys

    from fastapi_azure_auth.openid_config import HttpClientConfig

log = logging.getLogger('fastapi_azure_auth')


class AzureAuthorizationCodeBearerBase(SecurityBase):
    def __init__(
        self,
        app_client_id: str,
        auto_error: bool = True,
        tenant_id: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        multi_tenant: bool = False,
        leeway: int = 0,
        validate_iss: bool = True,
        iss_callable: Optional[Callable[[str], Awaitable[str]]] = None,
        allow_guest_users: bool = False,
        openid_config_use_app_id: bool = False,
        openapi_authorization_url: Optional[str] = None,
        openapi_token_url: Optional[str] = None,
        openid_config_url: Optional[str] = None,
        openapi_description: Optional[str] = None,
        scheme_name: str = "AzureAuthorizationCodeBearerBase",
        http_client_config: Optional["HttpClientConfig"] = None,
    ) -> None:
        """
        Initialize settings.

        :param app_client_id: str
            Your application client ID. This will be the `Web app` in Azure Entra ID
        :param auto_error: bool
            Whether to throw exceptions or return None on __call__.
        :param tenant_id: str
            Your Azure tenant ID, only needed for single tenant apps
        :param scopes: Optional[dict[str, str]
            Scopes, these are the ones you've configured in Azure Entra ID. Key is scope, value is a description.
            Example:
                {
                    f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user impersonation'
                }

        :param multi_tenant: bool
            Whether this is a multi tenant or single tenant application.
        :param leeway: int
            By adding leeway, you define a tolerance window in terms of seconds, allowing the token to be
            considered valid even if it falls within the leeway time before or after the "exp" or "nbf" times.
        :param validate_iss: bool
        **Only used for multi-tenant applications**
            Whether to validate the token `iss` (issuer) or not. This can be skipped to allow anyone to log in.
        :param iss_callable: Async Callable
        **Only used for multi-tenant application**
            Async function that has to accept a `tid` (tenant ID) and return a `iss` (issuer) or
             raise an InvalidIssuer exception
            This is required when validate_iss is set to `True`.

        :param allow_guest_users: bool
            Whether to allow guest users or not. Guest users can be added manually, or by other services, such as
            inviting them to a teams channel. Most developers do _not_ want guest users in their applications.

        :param openid_config_use_app_id: bool
            Set this to True if you're using claims-mapping. If you're unsure, leave at False.
            https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc#sample-response

        :param openapi_authorization_url: str
            Override OpenAPI authorization URL
        :param openapi_token_url: str
            Override OpenAPI token URL
        :param openid_config_url: str
            Override OpenID config URL (used for B2C tenants)
        :param openapi_description: str
            Override OpenAPI description
        :param scheme_name: str
            The name of the security scheme to be used in OpenAPI documentation.
            Default is 'AzureAuthorizationCodeBearerBase'.
        :param http_client_config: HttpClientConfig
            Configuration for the HTTP client used to fetch the OpenID configuration.
        """
        self.auto_error = auto_error
        # Validate settings, making sure there's no misconfigured dependencies out there
        if multi_tenant:
            if validate_iss and not callable(iss_callable):
                raise RuntimeError('`validate_iss` is enabled, so you must provide an `iss_callable`')
            elif iss_callable and 'tid' not in inspect.signature(iss_callable).parameters.keys():
                raise RuntimeError('`iss_callable` must accept `tid` as an argument')

        self.app_client_id: str = app_client_id
        self.multi_tenant: bool = multi_tenant
        self.openid_config: OpenIdConfig = OpenIdConfig(
            tenant_id=tenant_id,
            multi_tenant=self.multi_tenant,
            app_id=app_client_id if openid_config_use_app_id else None,
            config_url=openid_config_url or None,
            http_client_config=http_client_config,
        )

        self.leeway: int = leeway
        self.validate_iss: bool = validate_iss
        self.iss_callable: Optional[Callable[..., Any]] = iss_callable
        self.allow_guest_users = allow_guest_users
        # Define settings for `OAuth2AuthorizationCodeBearer` and OpenAPI Authorization
        self.authorization_url = openapi_authorization_url
        self.token_url = openapi_token_url
        if not self.authorization_url:
            if multi_tenant:
                self.authorization_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            else:
                self.authorization_url = (
                    f'https://login.microsoftonline.com/{self.openid_config.tenant_id}/oauth2/v2.0/authorize'
                )
        if not self.token_url:
            if multi_tenant:
                self.token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
            else:
                self.token_url = f'https://login.microsoftonline.com/{self.openid_config.tenant_id}/oauth2/v2.0/token'

        self.oauth = OAuth2AuthorizationCodeBearer(
            authorizationUrl=self.authorization_url,
            tokenUrl=self.token_url,
            scopes=scopes,
            scheme_name=scheme_name,
            description=openapi_description or '`Leave client_secret blank`',
            auto_error=True,  # We catch this exception in __call__
        )
        self.model = self.oauth.model

    async def __call__(self, request: HTTPConnection, security_scopes: SecurityScopes) -> Optional[User]:
        """
        Extends call to also validate the token.
        """
        try:
            access_token = await self.extract_access_token(request)
            try:
                if access_token is None:
                    raise InvalidRequest('No access token provided', request=request)
                # Extract header information of the token.
                header: dict[str, Any] = get_unverified_header(access_token)
                claims: dict[str, Any] = get_unverified_claims(access_token)
            except Exception as error:
                log.warning('Malformed token received. %s. Error: %s', access_token, error, exc_info=True)
                raise Unauthorized(
                    detail='Invalid token format',
                    client_id=self.app_client_id,
                    authorization_url=self.authorization_url,
                    request=request,
                ) from error

            user_is_guest: bool = is_guest(claims=claims)
            if not self.allow_guest_users and user_is_guest:
                log.info('User denied, is a guest user', claims)
                raise Forbidden(detail='Guest users not allowed', request=request)

            for scope in security_scopes.scopes:
                token_scope_string = claims.get('scp', '')
                log.debug('Scopes: %s', token_scope_string)
                if not isinstance(token_scope_string, str):
                    raise Forbidden('Token contains invalid formatted scopes', request=request)

                token_scopes = token_scope_string.split(' ')
                if scope not in token_scopes:
                    raise Forbidden('Required scope missing', request=request)
            # Load new config if old
            await self.openid_config.load_config()

            if self.multi_tenant and self.validate_iss and self.iss_callable:
                iss = await self.iss_callable(tid=claims.get('tid'))
            else:
                iss = self.openid_config.issuer

            # Use the `kid` from the header to find a matching signing key to use
            try:
                if key := self.openid_config.signing_keys.get(header.get('kid', '')):
                    # We require and validate all fields in an Azure Entra ID token
                    required_claims = ['exp', 'aud', 'iat', 'nbf', 'sub']
                    if self.validate_iss:
                        required_claims.append('iss')

                    options = {
                        'verify_signature': True,
                        'verify_aud': True,
                        'verify_iat': True,
                        'verify_exp': True,
                        'verify_nbf': True,
                        'verify_iss': self.validate_iss,
                        'require': required_claims,
                    }
                    # Validate token
                    token = self.validate(access_token=access_token, iss=iss, key=key, options=options)
                    # Attach the user to the request. Can be accessed through `request.state.user`
                    user: User = User(
                        **{**token, 'claims': token, 'access_token': access_token, 'is_guest': user_is_guest}
                    )
                    request.state.user = user
                    return user
            except (
                InvalidAudienceError,
                InvalidIssuerError,
                InvalidIssuedAtError,
                ImmatureSignatureError,
                MissingRequiredClaimError,
            ) as error:
                log.info('Token contains invalid claims. %s', error)
                raise Unauthorized(detail='Token contains invalid claims', request=request) from error
            except ExpiredSignatureError as error:
                log.info('Token signature has expired. %s', error)
                raise Unauthorized(detail='Token signature has expired', request=request) from error
            except InvalidTokenError as error:
                log.warning('Invalid token. Error: %s', error, exc_info=True)
                raise Unauthorized(detail='Unable to validate token', request=request) from error
            except Exception as error:
                # Extra failsafe in case of a bug in a future version of the jwt library
                log.exception('Unable to process jwt token. Uncaught error: %s', error)
                raise Unauthorized(detail='Unable to process token', request=request) from error
            log.warning('Unable to verify token. No signing keys found')
            raise Unauthorized(detail='Unable to verify token, no signing keys found', request=request)
        except (
            InvalidAuthHttp,
            InvalidAuthWebSocket,
            InvalidRequestHttp,
            UnauthorizedHttp,
            UnauthorizedWebSocket,
            ForbiddenHttp,
            ForbiddenWebSocket,
            HTTPException,
        ):
            if not self.auto_error:
                return None
            raise
        except Exception as error:
            if not self.auto_error:
                return None
            raise InvalidRequest(detail='Unable to validate token', request=request) from error

    async def extract_access_token(self, request: HTTPConnection) -> Optional[str]:
        """
        Extracts the access token from the request.
        """
        return await self.oauth(request=request)  # type: ignore[arg-type]

    def validate(
        self, access_token: str, key: 'AllowedPublicKeys', iss: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates the token using the provided key and options.
        """
        alg = 'RS256'
        return dict(
            jwt.decode(
                access_token,
                key=key,
                algorithms=[alg],
                audience=self.app_client_id,
                issuer=iss,
                leeway=self.leeway,
                options=options,
            )
        )


class SingleTenantAzureAuthorizationCodeBearer(AzureAuthorizationCodeBearerBase):
    def __init__(
        self,
        app_client_id: str,
        tenant_id: str,
        auto_error: bool = True,
        scopes: Optional[Dict[str, str]] = None,
        leeway: int = 0,
        allow_guest_users: bool = False,
        openid_config_use_app_id: bool = False,
        openapi_authorization_url: Optional[str] = None,
        openapi_token_url: Optional[str] = None,
        openapi_description: Optional[str] = None,
        scheme_name: str = "AzureAD_PKCE_single_tenant",
        http_client_config: Optional["HttpClientConfig"] = None,
    ) -> None:
        """
        Initialize settings for a single tenant application.

        :param app_client_id: str
            Your application client ID. This will be the `Web app` in Azure Entra ID
        :param tenant_id: str
            Your Azure tenant ID, only needed for single tenant apps
        :param auto_error: bool
            Whether to throw exceptions or return None on __call__.
        :param scopes: Optional[dict[str, str]
            Scopes, these are the ones you've configured in Azure Entra ID. Key is scope, value is a description.
            Example:
                {
                    f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user impersonation'
                }

        :param leeway: int
            By adding leeway, you define a tolerance window in terms of seconds, allowing the token to be
            considered valid even if it falls within the leeway time before or after the "exp" or "nbf" times.

        :param allow_guest_users: bool
            Whether to allow guest users or not. Guest users can be added manually, or by other services, such as
            inviting them to a teams channel. Most developers do _not_ want guest users in their applications.

        :param openid_config_use_app_id: bool
            Set this to True if you're using claims-mapping. If you're unsure, leave at False.
            https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc#sample-response

        :param openapi_authorization_url: str
            Override OpenAPI authorization URL
        :param openapi_token_url: str
            Override OpenAPI token URL
        :param openapi_description: str
            Override OpenAPI description
        :param scheme_name: str
            The name of the security scheme to be used in OpenAPI documentation.
            Default is 'AzureAD_PKCE_single_tenant'.
        :param http_client_config: HttpClientConfig
            Configuration for the HTTP client used to fetch the OpenID configuration.
        """
        super().__init__(
            app_client_id=app_client_id,
            auto_error=auto_error,
            tenant_id=tenant_id,
            scopes=scopes,
            leeway=leeway,
            allow_guest_users=allow_guest_users,
            openid_config_use_app_id=openid_config_use_app_id,
            openapi_authorization_url=openapi_authorization_url,
            openapi_token_url=openapi_token_url,
            openapi_description=openapi_description,
            http_client_config=http_client_config,
        )
        self.scheme_name: str = scheme_name


class MultiTenantAzureAuthorizationCodeBearer(AzureAuthorizationCodeBearerBase):
    def __init__(
        self,
        app_client_id: str,
        auto_error: bool = True,
        scopes: Optional[Dict[str, str]] = None,
        leeway: int = 0,
        validate_iss: bool = True,
        iss_callable: Optional[Callable[[str], Awaitable[str]]] = None,
        allow_guest_users: bool = False,
        openid_config_use_app_id: bool = False,
        openapi_authorization_url: Optional[str] = None,
        openapi_token_url: Optional[str] = None,
        openapi_description: Optional[str] = None,
        scheme_name: str = "AzureAD_PKCE_multi_tenant",
        http_client_config: Optional["HttpClientConfig"] = None,
    ) -> None:
        """
        Initialize settings for a multi-tenant application.

        :param app_client_id: str
            Your application client ID. This will be the `Web app` in Azure Entra ID
        :param auto_error: bool
            Whether to throw exceptions or return None on __call__.
        :param scopes: Optional[dict[str, str]
            Scopes, these are the ones you've configured in Azure Entra ID. Key is scope, value is a description.
            Example:
                {
                    f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user impersonation'
                }

        :param leeway: int
            By adding leeway, you define a tolerance window in terms of seconds, allowing the token to be
            considered valid even if it falls within the leeway time before or after the "exp" or "nbf" times.

        :param validate_iss: bool
            Whether to validate the token `iss` (issuer) or not. This can be skipped to allow anyone to log in.
        :param iss_callable: Async Callable
            Async function that has to accept a `tid` (tenant ID) and return a `iss` (issuer) or
             raise an InvalidIssuer exception
            This is required when validate_iss is set to `True`.

        :param allow_guest_users: bool
            Whether to allow guest users or not. Guest users can be added manually, or by other services, such as
            inviting them to a teams channel. Most developers do _not_ want guest users in their applications.

        :param openid_config_use_app_id: bool
            Set this to True if you're using claims-mapping. If you're unsure, leave at False.
            https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc#sample-response

        :param openapi_authorization_url: str
            Override OpenAPI authorization URL
        :param openapi_token_url: str
            Override OpenAPI token URL
        :param openapi_description: str
            Override OpenAPI description
        :param scheme_name: str
            The name of the security scheme to be used in OpenAPI documentation.
            Default is 'AzureAD_PKCE_multi_tenant'.
        :param http_client_config: HttpClientConfig
            Configuration for the HTTP client used to fetch the OpenID configuration.
        """
        super().__init__(
            app_client_id=app_client_id,
            auto_error=auto_error,
            scopes=scopes,
            leeway=leeway,
            validate_iss=validate_iss,
            iss_callable=iss_callable,
            allow_guest_users=allow_guest_users,
            multi_tenant=True,
            openid_config_use_app_id=openid_config_use_app_id,
            openapi_authorization_url=openapi_authorization_url,
            openapi_token_url=openapi_token_url,
            openapi_description=openapi_description,
            http_client_config=http_client_config,
        )
        self.scheme_name: str = scheme_name


class B2CMultiTenantAuthorizationCodeBearer(AzureAuthorizationCodeBearerBase):
    def __init__(
        self,
        app_client_id: str,
        auto_error: bool = True,
        scopes: Optional[Dict[str, str]] = None,
        leeway: int = 0,
        validate_iss: bool = True,
        iss_callable: Optional[Callable[[str], Awaitable[str]]] = None,
        openid_config_use_app_id: bool = False,
        openid_config_url: Optional[str] = None,
        openapi_authorization_url: Optional[str] = None,
        openapi_token_url: Optional[str] = None,
        openapi_description: Optional[str] = None,
        scheme_name: str = "AzureAD_PKCE_B2C_multi_tenant",
        http_client_config: Optional["HttpClientConfig"] = None,
    ) -> None:
        """
        Initialize settings for a B2C multi-tenant application.
        :param app_client_id: str
            Your application client ID. This will be the `Web app` in Azure Entra ID
        :param openid_config_url: str
            Override OpenID config URL (used for B2C tenants)
        :param auto_error: bool
            Whether to throw exceptions or return None on __call__.
        :param scopes: Optional[dict[str, str]
            Scopes, these are the ones you've configured in Azure Entra ID. Key is scope, value is a description.
            Example:
                {
                    f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user impersonation'
                }

        :param leeway: int
            By adding leeway, you define a tolerance window in terms of seconds, allowing the token to be
            considered valid even if it falls within the leeway time before or after the "exp" or "nbf" times.

        :param validate_iss: bool
            Whether to validate the token `iss` (issuer) or not. This can be skipped to allow anyone to log in.
        :param iss_callable: Async Callable
            Async function that has to accept a `tid` (tenant ID) and return a `iss` (issuer) or
             raise an InvalidIssuer exception
            This is required when validate_iss is set to `True`.
        :param openid_config_use_app_id: bool
            Set this to True if you're using claims-mapping. If you're unsure, leave at False.
            https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc#sample-response
        :param openapi_authorization_url: str
            Override OpenAPI authorization URL
        :param openapi_token_url: str
            Override OpenAPI token URL
        :param openapi_description: str
            Override OpenAPI description
        :param scheme_name: str
            The name of the security scheme to be used in OpenAPI documentation.
            Default is 'AzureAD_PKCE_B2C_multi_tenant'.
        :param http_client_config: HttpClientConfig
            Configuration for the HTTP client used to fetch the OpenID configuration.
        """
        super().__init__(
            app_client_id=app_client_id,
            auto_error=auto_error,
            scopes=scopes,
            leeway=leeway,
            validate_iss=validate_iss,
            iss_callable=iss_callable,
            multi_tenant=True,
            allow_guest_users=True,
            openid_config_use_app_id=openid_config_use_app_id,
            openid_config_url=openid_config_url,
            openapi_authorization_url=openapi_authorization_url,
            openapi_token_url=openapi_token_url,
            openapi_description=openapi_description,
            http_client_config=http_client_config,
        )
        self.scheme_name: str = scheme_name
