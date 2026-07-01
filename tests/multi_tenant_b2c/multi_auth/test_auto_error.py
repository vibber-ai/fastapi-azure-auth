import pytest
from httpx import ASGITransport, AsyncClient

from demo_project.main import app


@pytest.mark.anyio
async def test_api_key_valid_key(multi_tenant_app, mock_openid_and_keys, freezer):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test', headers={'TEST-API-KEY': 'JonasIsCool'}
    ) as ac:
        response = await ac.get('api/v1/hello-multi-auth-b2c')
        assert response.json() == {'api_key': True, 'azure_auth': False}
        assert response.status_code == 200


@pytest.mark.anyio
async def test_api_key_but_invalid_key(multi_tenant_app, mock_openid_and_keys, freezer):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test', headers={'TEST-API-KEY': 'JonasIsNotCool'}
    ) as ac:
        response = await ac.get('api/v1/hello-multi-auth-b2c')
        assert response.json() == {
            'detail': {'error': 'invalid_token', 'message': 'You must either provide a valid bearer token or API key'}
        }
        assert response.status_code == 401
