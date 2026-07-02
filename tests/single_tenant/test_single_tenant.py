import time
from datetime import datetime, timedelta

import pytest
from httpx2 import ASGITransport, AsyncClient

from demo_project.main import app
from fastapi_azure_auth.auth import AzureAuthorizationCodeBearerBase
from tests.utils import (
    build_access_token,
    build_access_token_expired,
    build_access_token_guest_user,
    build_access_token_invalid_claims,
    build_access_token_invalid_scopes,
    build_access_token_normal_user,
    build_evil_access_token,
)


@pytest.mark.anyio
async def test_normal_user(single_tenant_app, mock_openid_and_keys):
    issued_at = int(time.time())
    expires = issued_at + 3600
    access_token = build_access_token()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test', headers={'Authorization': f'Bearer {access_token}'}
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {
        'hello': 'world',
        'user': {
            'access_token': access_token,
            'aud': 'oauth299-9999-9999-abcd-efghijkl1234567890',
            'claims': {
                '_claim_names': {'groups': 'src1'},
                '_claim_sources': {
                    'src1': {'endpoint': 'https://graph.windows.net/vibber_tenant_id/users/JONASGUID/getMemberObjects'}
                },
                'aio': 'some long val',
                'aud': 'oauth299-9999-9999-abcd-efghijkl1234567890',
                'azp': 'some long val',
                'azpacr': '0',
                'exp': expires,
                'iat': issued_at,
                'iss': 'https://login.microsoftonline.com/vibber_tenant/v2.0',
                'name': 'Jonas Krüger Svensson / Vibber AS',
                'nbf': issued_at,
                'oid': '22222222-2222-2222-2222-222222222222',
                'preferred_username': 'jonas@vibber.ai',
                'rh': 'some long val',
                'roles': ['AdminUser'],
                'scp': 'user_impersonation',
                'sub': 'some long val',
                'tid': 'vibber_tenant_id',
                'uti': 'abcdefghijkl-mnopqrstu',
                'ver': '2.0',
                'wids': ['some long val'],
            },
            'is_guest': False,
            'name': 'Jonas Krüger Svensson / Vibber AS',
            'roles': ['AdminUser'],
            'scp': ['user_impersonation'],
            'tid': 'vibber_tenant_id',
            'oid': '22222222-2222-2222-2222-222222222222',
            'sub': 'some long val',
            'acct': None,
            'acr': None,
            'aio': 'some long val',
            'amr': [],
            'appid': None,
            'appidacr': None,
            'auth_time': None,
            'azp': 'some long val',
            'azpacr': '0',
            'ctry': None,
            'email': None,
            'exp': expires,
            'family_name': None,
            'fwd': None,
            'given_name': None,
            'groups': [],
            'iat': issued_at,
            'idp': None,
            'idtyp': None,
            'in_corp': None,
            'ipaddr': None,
            'iss': 'https://login.microsoftonline.com/vibber_tenant/v2.0',
            'login_hint': None,
            'nbf': issued_at,
            'onprem_sid': None,
            'preferred_username': 'jonas@vibber.ai',
            'pwd_exp': None,
            'pwd_url': None,
            'rh': 'some long val',
            'sid': None,
            'tenant_ctry': None,
            'tenant_region_scope': None,
            'unique_name': None,
            'upn': None,
            'uti': 'abcdefghijkl-mnopqrstu',
            'ver': '2.0',
            'verified_primary_email': [],
            'verified_secondary_email': [],
            'vnet': None,
            'wids': ['some long val'],
            'xms_pdl': None,
            'xms_pl': None,
            'xms_tpl': None,
            'ztdid': None,
        },
    }


@pytest.mark.anyio
async def test_no_keys_to_decode_with(single_tenant_app, mock_openid_and_empty_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {
        'detail': {'error': 'invalid_token', 'message': 'Unable to verify token, no signing keys found'}
    }
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.anyio
async def test_normal_user_rejected(single_tenant_app, mock_openid_and_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_normal_user()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'insufficient_scope', 'message': 'User is not an AdminUser'}}
    assert response.status_code == 403


@pytest.mark.anyio
async def test_guest_user_rejected(single_tenant_app, mock_openid_and_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_guest_user()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'insufficient_scope', 'message': 'Guest users not allowed'}}
    assert response.status_code == 403


@pytest.mark.anyio
async def test_invalid_token_claims(single_tenant_app, mock_openid_and_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_invalid_claims()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Token contains invalid claims'}}
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.anyio
async def test_no_valid_keys_for_token(single_tenant_app, mock_openid_and_no_valid_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_invalid_claims()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {
        'detail': {'error': 'invalid_token', 'message': 'Unable to verify token, no signing keys found'}
    }
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.anyio
async def test_no_valid_scopes(single_tenant_app, mock_openid_and_no_valid_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_invalid_scopes()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'insufficient_scope', 'message': 'Required scope missing'}}
    assert response.status_code == 403


@pytest.mark.anyio
async def test_no_valid_invalid_scope(single_tenant_app, mock_openid_and_no_valid_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_invalid_scopes()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'insufficient_scope', 'message': 'Required scope missing'}}
    assert response.status_code == 403


@pytest.mark.anyio
async def test_no_valid_invalid_formatted_scope(single_tenant_app, mock_openid_and_no_valid_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_invalid_scopes(scopes=None)},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {
        'detail': {'error': 'insufficient_scope', 'message': 'Token contains invalid formatted scopes'}
    }
    assert response.status_code == 403
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.anyio
async def test_expired_token(single_tenant_app, mock_openid_and_keys):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_expired()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Token signature has expired'}}
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.anyio
async def test_evil_token(single_tenant_app, mock_openid_and_keys):
    """Kid matches what we expect, but it's not signed correctly"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_evil_access_token()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Unable to validate token'}}
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.anyio
async def test_malformed_token(single_tenant_app, mock_openid_and_keys):
    """A short token, that only has a broken header"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cI6IkpXVCJ9'},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Invalid token format'}}
    assert response.status_code == 401
    assert (
        response.headers['www-authenticate']
        == 'Bearer, authorization_uri="https://login.microsoftonline.com/vibber_tenant_id/oauth2/v2.0/authorize", client_id="oauth299-9999-9999-abcd-efghijkl1234567890"'
    )


@pytest.mark.anyio
async def test_only_header(single_tenant_app, mock_openid_and_keys):
    """Only header token, with a matching kid, so the rest of the logic will be called, but can't be validated"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={
            'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6InJlYWwgdGh1bWJ'
            'wcmludCIsInR5cCI6IkpXVCIsIng1dCI6ImFub3RoZXIgdGh1bWJwcmludCJ9'
        },  # {'kid': 'real thumbprint', 'x5t': 'another thumbprint'}
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Invalid token format'}}
    assert response.status_code == 401
    assert (
        response.headers['www-authenticate']
        == 'Bearer, authorization_uri="https://login.microsoftonline.com/vibber_tenant_id/oauth2/v2.0/authorize", client_id="oauth299-9999-9999-abcd-efghijkl1234567890"'
    )


@pytest.mark.anyio
async def test_none_token(single_tenant_app, mock_openid_and_keys, mocker):
    mocker.patch.object(AzureAuthorizationCodeBearerBase, 'extract_access_token', return_value=None)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_expired()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Invalid token format'}}
    assert response.status_code == 401
    assert (
        response.headers['www-authenticate']
        == 'Bearer, authorization_uri="https://login.microsoftonline.com/vibber_tenant_id/oauth2/v2.0/authorize", client_id="oauth299-9999-9999-abcd-efghijkl1234567890"'
    )


@pytest.mark.anyio
async def test_exception_raised(single_tenant_app, mock_openid_and_keys, mocker):
    mocker.patch.object(AzureAuthorizationCodeBearerBase, 'validate', side_effect=ValueError('lol'))
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token_expired()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Unable to process token'}}
    assert response.status_code == 401
    print(f'header: {response.headers.get("www-authenticate")}')
    assert response.headers['www-authenticate'] == 'Bearer'


@pytest.mark.anyio
async def test_change_of_keys_works(single_tenant_app, mock_openid_ok_then_empty, freezer):
    """
    * Do a successful request.
    * Set time to 25 hours later, so that a new OpenAPI config has to be fetched
    * Ensure new keys returned is an empty list, so the next request shouldn't work.
    * Generate a new, valid token
    * Do request
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token()},
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.status_code == 200

    freezer.move_to(datetime.now() + timedelta(hours=25))  # The keys fetched are now outdated

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
        headers={'Authorization': 'Bearer ' + build_access_token()},
    ) as ac:
        second_resonse = await ac.get('api/v1/hello')
    assert second_resonse.json() == {
        'detail': {'error': 'invalid_token', 'message': 'Unable to verify token, no signing keys found'}
    }
    assert second_resonse.status_code == 401
    assert 'www-authenticate' not in response.headers


@pytest.mark.anyio
async def test_authentication_params_from_header(single_tenant_app):
    """
    * Send request with "Authorization: Bearer"
    * Validate response provides authorization uri and client id in header
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test', headers={'Authorization': 'Bearer'}
    ) as ac:
        response = await ac.get('api/v1/hello')
    assert response.status_code == 401
    assert (
        response.headers['www-authenticate']
        == 'Bearer, authorization_uri="https://login.microsoftonline.com/vibber_tenant_id/oauth2/v2.0/authorize", client_id="oauth299-9999-9999-abcd-efghijkl1234567890"'
    )
