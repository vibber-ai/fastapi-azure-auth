from fastapi_azure_auth.auth import (  # noqa: F401
    B2CMultiTenantAuthorizationCodeBearer as B2CMultiTenantAuthorizationCodeBearer,
    MultiTenantAzureAuthorizationCodeBearer as MultiTenantAzureAuthorizationCodeBearer,
    SingleTenantAzureAuthorizationCodeBearer as SingleTenantAzureAuthorizationCodeBearer,
)
from fastapi_azure_auth.openid_config import HttpClientConfig as HttpClientConfig  # noqa: F401

__version__ = '5.3.0'
