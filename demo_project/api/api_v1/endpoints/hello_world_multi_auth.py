from fastapi import APIRouter, Depends, Request

from demo_project.api.dependencies import multi_auth, multi_auth_b2c
from demo_project.schemas.hello_world import TokenType
from fastapi_azure_auth.user import User

router = APIRouter()


@router.get(
    '/hello-multi-auth',
    response_model=TokenType,
    summary='Say hello with an API key',
    name='hello_world_api_key',
    operation_id='helloWorldApiKeyMultiAuth',
)
async def world(request: Request, auth: str | User = Depends(multi_auth)) -> dict[str, bool]:
    """
    Wonder how this auth is done?
    """
    if isinstance(auth, str):
        # An API key was used
        return {'api_key': True, 'azure_auth': False}
    return {'api_key': False, 'azure_auth': True}


@router.get(
    '/hello-multi-auth-b2c',
    response_model=TokenType,
    summary='Say hello with an API key',
    name='hello_world_api_key',
    operation_id='helloWorldApiKeyMultiAuthB2C',
)
async def world_b2c(request: Request, auth: str | User = Depends(multi_auth_b2c)) -> dict[str, bool]:
    """
    Wonder how this auth is done?
    """
    if isinstance(auth, str):
        # An API key was used
        return {'api_key': True, 'azure_auth': False}
    return {'api_key': False, 'azure_auth': True}
