from fastapi_azure_auth.auth import (  # noqa: F401
    B2CMultiTenantAuthorizationCodeBearer as B2CMultiTenantAuthorizationCodeBearer,
    MultiTenantAzureAuthorizationCodeBearer as MultiTenantAzureAuthorizationCodeBearer,
    SingleTenantAzureAuthorizationCodeBearer as SingleTenantAzureAuthorizationCodeBearer,
)

__version__ = '5.2.1'
