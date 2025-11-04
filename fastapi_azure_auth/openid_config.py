import logging
import ssl
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from typing import TYPE_CHECKING, Any, Dict, List, NotRequired, Optional, TypedDict

import jwt
from fastapi import HTTPException, status
from httpx import AsyncClient

if TYPE_CHECKING:  # pragma: no cover
    from jwt.algorithms import AllowedPublicKeys

log = logging.getLogger('fastapi_azure_auth')


class HttpClientConfig(TypedDict):
    verify: NotRequired[ssl.SSLContext]


class OpenIdConfig:
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        multi_tenant: bool = False,
        app_id: Optional[str] = None,
        config_url: Optional[str] = None,
        http_client_config: Optional[HttpClientConfig] = None,
    ) -> None:
        self.tenant_id: Optional[str] = tenant_id
        self._config_timestamp: Optional[datetime] = None
        self.multi_tenant: bool = multi_tenant
        self.app_id = app_id
        self.config_url = config_url
        self.http_client_config: HttpClientConfig = (
            http_client_config or HttpClientConfig()
        )

        self.authorization_endpoint: str
        self.signing_keys: dict[str, 'AllowedPublicKeys']
        self.token_endpoint: str
        self.issuer: str

    async def load_config(self) -> None:
        """
        Loads config from the Intility openid-config endpoint if it's over 24 hours old (or don't exist)
        """
        refresh_time = datetime.now() - timedelta(hours=24)
        if not self._config_timestamp or self._config_timestamp < refresh_time:
            try:
                log.debug('Loading Azure Entra ID OpenID configuration.')
                await self._load_openid_config()
                self._config_timestamp = datetime.now()
            except Exception as error:
                log.exception('Unable to fetch OpenID configuration from Azure Entra ID. Error: %s', error)
                # We can't fetch an up to date openid-config, so authentication will not work.
                if self._config_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Connection to Azure Entra ID is down. Unable to fetch provider configuration',
                        headers={'WWW-Authenticate': 'Bearer'},
                    ) from error

                else:
                    raise RuntimeError(f'Unable to fetch provider information. {error}') from error

            log.info('fastapi-azure-auth loaded settings from Azure Entra ID.')
            log.info('authorization endpoint: %s', self.authorization_endpoint)
            log.info('token endpoint:         %s', self.token_endpoint)
            log.info('issuer:                 %s', self.issuer)

    async def _load_openid_config(self) -> None:
        """
        Load openid config, fetch signing keys
        """
        path = 'common' if self.multi_tenant else self.tenant_id

        if self.config_url:
            config_url = self.config_url
        else:
            config_url = f'https://login.microsoftonline.com/{path}/v2.0/.well-known/openid-configuration'
        if self.app_id:
            config_url += f'?appid={self.app_id}'

        async with AsyncClient(timeout=10, **self.http_client_config) as client:
            log.info('Fetching OpenID Connect config from %s', config_url)
            openid_response = await client.get(config_url)
            openid_response.raise_for_status()
            openid_cfg = openid_response.json()

            self.authorization_endpoint = openid_cfg['authorization_endpoint']
            self.token_endpoint = openid_cfg['token_endpoint']
            self.issuer = openid_cfg['issuer']

            jwks_uri = openid_cfg['jwks_uri']
            log.info('Fetching jwks from %s', jwks_uri)
            jwks_response = await client.get(jwks_uri)
            jwks_response.raise_for_status()
            self._load_keys(jwks_response.json()['keys'])

    def _load_keys(self, keys: List[Dict[str, Any]]) -> None:
        """
        Create certificates based on signing keys and store them
        """
        self.signing_keys = {}
        for key in keys:
            if key.get('use') == 'sig':  # Only care about keys that are used for signatures, not encryption
                log.debug('Loading public key from certificate: %s', key)
                cert_obj = jwt.PyJWK(key, 'RS256')
                if kid := key.get('kid'):  # In case a key would not have a thumbprint we can match, we don't want it.
                    self.signing_keys[kid] = cert_obj.key
