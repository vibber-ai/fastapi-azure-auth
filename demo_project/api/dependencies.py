import logging
from datetime import datetime, timedelta

from fastapi import Depends
from fastapi.security.api_key import APIKeyHeader

from demo_project.core.config import settings
from fastapi_azure_auth import (
    B2CMultiTenantAuthorizationCodeBearer,
    MultiTenantAzureAuthorizationCodeBearer,
    SingleTenantAzureAuthorizationCodeBearer,
)
from fastapi_azure_auth.exceptions import ForbiddenHttp, UnauthorizedHttp
from fastapi_azure_auth.user import User

log = logging.getLogger(__name__)


azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    scopes={f'api://{settings.APP_CLIENT_ID}/user_impersonation': '**No client secret needed, leave blank**'},
    tenant_id=settings.TENANT_ID,
)


async def validate_is_admin_user(user: User = Depends(azure_scheme)) -> None:
    """
    Validate that a user is in the `AdminUser` role in order to access the API.
    Raises a 401 authentication error if not.
    """
    if 'AdminUser' not in user.roles:
        raise ForbiddenHttp('User is not an AdminUser')


class IssuerFetcher:
    def __init__(self) -> None:
        """
        Example class for multi tenant apps, that caches issuers for an hour
        """
        self.tid_to_iss: dict[str, str] = {}
        self._config_timestamp: datetime | None = None

    async def __call__(self, tid: str) -> str:
        """
        Check if memory cache needs to be updated or not, and then returns an issuer for a given tenant
        :raises Unauthorized when it's not a valid tenant
        """
        refresh_time = datetime.now() - timedelta(hours=1)
        if not self._config_timestamp or self._config_timestamp < refresh_time:
            self._config_timestamp = datetime.now()
            # logic to find your allowed tenants and it's issuers here
            # (This example cache in memory for 1 hour)
            self.tid_to_iss = {
                'vibber_tenant_id': 'https://login.microsoftonline.com/vibber_tenant/v2.0',
            }
        try:
            return self.tid_to_iss[tid]
        except Exception as error:
            log.exception('`iss` not found for `tid` %s. Error %s', tid, error)
            raise UnauthorizedHttp('You must be a Vibber customer to access this resource')


issuer_fetcher = IssuerFetcher()

azure_scheme_auto_error_false = MultiTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    scopes={
        f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'User impersonation',
    },
    validate_iss=True,
    iss_callable=issuer_fetcher,
    auto_error=False,
)

azure_scheme_auto_error_false_b2c = B2CMultiTenantAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    openapi_authorization_url=str(settings.AUTH_URL),
    openapi_token_url=str(settings.TOKEN_URL),
    openid_config_url=str(settings.CONFIG_URL),
    scopes={
        f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'User impersonation',
    },
    validate_iss=True,
    iss_callable=issuer_fetcher,
    auto_error=False,
)


api_key_auth_auto_error_false = APIKeyHeader(name='TEST-API-KEY', auto_error=False)


async def multi_auth(
    azure_auth: User | None = Depends(azure_scheme_auto_error_false),
    api_key: str | None = Depends(api_key_auth_auto_error_false),
) -> User | str:
    """
    Example implementation.
    """
    if azure_auth:
        return azure_auth
    if api_key == 'JonasIsCool':
        return api_key
    raise UnauthorizedHttp('You must either provide a valid bearer token or API key')


async def multi_auth_b2c(
    azure_auth: User | None = Depends(azure_scheme_auto_error_false_b2c),
    api_key: str | None = Depends(api_key_auth_auto_error_false),
) -> User | str:
    """
    Example implementation.
    """
    if azure_auth:
        return azure_auth
    if api_key == 'JonasIsCool':
        return api_key
    raise UnauthorizedHttp('You must either provide a valid bearer token or API key')
