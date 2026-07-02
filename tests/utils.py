import time

import jwt
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_private_key():
    """
    Generate a private key
    """
    return rsa.generate_private_key(backend=crypto_default_backend(), public_exponent=65537, key_size=2048)


def build_access_token():
    """
    Build an access token, coming from the tenant ID we expect
    """
    return do_build_access_token(tenant_id='vibber_tenant_id')


def build_access_token_normal_user():
    """
    Build an access token, coming from the tenant ID we expect, but not an admin user. (Only used to test dependency)
    """
    return do_build_access_token(tenant_id='vibber_tenant_id', admin=False)


def build_access_token_guest_user():
    """
    Build an access token, coming from the tenant ID we expect, but not an admin user. (Only used to test dependency)
    """
    return do_build_access_token(tenant_id='vibber_tenant_id', admin=True, guest_user=True)


def build_evil_access_token():
    """
    Build an access token, but signed with an invalid key (not matching its `kid`
    """
    return do_build_access_token(tenant_id='vibber_tenant_id', evil=True)


def build_access_token_invalid_claims():
    """
    Build an access token, but with invalid claims (audience does not match)
    """
    return do_build_access_token(tenant_id='vibber_tenant_id', aud='Jonas')


def build_access_token_invalid_scopes(scopes='not_user_impersonation'):
    """
    Build an access token, but with invalid scopes (not `user_impersonation`)
    """
    return do_build_access_token(tenant_id='vibber_tenant_id', scopes=scopes)


def build_access_token_expired():
    """
    Build an access token, coming from the tenant ID we expect
    """
    return do_build_access_token(tenant_id='vibber_tenant_id', expired=True)


def do_build_access_token(
    tenant_id: str | None = None,
    aud: str | None = None,
    expired: bool = False,
    evil: bool = False,
    admin: bool = True,
    scopes: str = 'user_impersonation',
    guest_user=False,
):
    """
    Build the access token and encode it with the signing key.
    """
    issued_at = int(time.time())
    expires = issued_at - 1 if expired else issued_at + 3600
    claims = {
        'aud': aud or 'oauth299-9999-9999-abcd-efghijkl1234567890',
        'iss': 'https://login.microsoftonline.com/vibber_tenant/v2.0',
        'iat': issued_at,
        'nbf': issued_at,
        'exp': expires,
        '_claim_names': {'groups': 'src1'},
        '_claim_sources': {
            'src1': {'endpoint': f'https://graph.windows.net/{tenant_id}/users/JONASGUID/getMemberObjects'}
        },
        'aio': 'some long val',
        'azp': 'some long val',
        'azpacr': '0',
        'name': 'Jonas Krüger Svensson / Vibber AS',
        'oid': '22222222-2222-2222-2222-222222222222',
        'preferred_username': 'jonas@vibber.ai',
        'rh': 'some long val',
        'scp': scopes,
        'sub': 'some long val',
        'tid': tenant_id,
        'uti': 'abcdefghijkl-mnopqrstu',
        'ver': '2.0',
        'wids': ['some long val'],
        'roles': ['AdminUser' if admin else 'NormalUser'],
    }
    if guest_user:
        claims['idp'] = 'https://sts.windows.net/e49ee8b0-4ec8-486f-93f3-bedaa281a154/'

    signing_key = signing_key_a if evil else signing_key_b
    return jwt.encode(
        claims,
        signing_key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            crypto_serialization.NoEncryption(),
        ),
        algorithm='RS256',
        headers={'kid': 'real thumbprint', 'x5t': 'real thumbprint'},
    )


def build_openid_keys(empty_keys: bool = False, no_valid_keys: bool = False) -> dict:
    """
    Build OpenID keys which we'll host at https://login.microsoftonline.com/common/discovery/keys
    """
    if empty_keys:
        return {'keys': []}
    elif no_valid_keys:
        return {
            'keys': [
                {
                    'use': 'sig',
                    'kid': 'dummythumbprint',
                    'x5t': 'dummythumbprint',
                    **jwt.algorithms.RSAAlgorithm.to_jwk(
                        signing_key_a,
                        as_dict=True,
                    ),
                }
            ]
        }
    else:
        return {
            'keys': [
                {
                    'use': 'sig',
                    'kid': 'dummythumbprint',
                    'x5t': 'dummythumbprint',
                    **jwt.algorithms.RSAAlgorithm.to_jwk(
                        signing_key_a.public_key(),
                        as_dict=True,
                    ),
                },
                {
                    'use': 'sig',
                    'kid': 'real thumbprint',
                    'x5t': 'real thumbprint',
                    **jwt.algorithms.RSAAlgorithm.to_jwk(
                        signing_key_b.public_key(),
                        as_dict=True,
                    ),
                },
            ]
        }


def openid_configuration() -> dict:
    return {
        'token_endpoint': 'https://login.microsoftonline.com/vibber_tenant/oauth2/v2.0/token',
        'token_endpoint_auth_methods_supported': ['client_secret_post', 'private_key_jwt', 'client_secret_basic'],
        'jwks_uri': 'https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys',
        'response_modes_supported': ['query', 'fragment', 'form_post'],
        'subject_types_supported': ['pairwise'],
        'id_token_signing_alg_values_supported': ['RS256'],
        'response_types_supported': ['code', 'id_token', 'code id_token', 'id_token token'],
        'scopes_supported': ['openid', 'profile', 'email', 'offline_access'],
        'issuer': 'https://login.microsoftonline.com/vibber_tenant/v2.0',
        'request_uri_parameter_supported': False,
        'userinfo_endpoint': 'https://graph.microsoft.com/oidc/userinfo',
        'authorization_endpoint': 'https://login.microsoftonline.com/vibber_tenant/oauth2/v2.0/authorize',
        'device_authorization_endpoint': 'https://login.microsoftonline.com/vibber_tenant/oauth2/v2.0/devicecode',
        'http_logout_supported': True,
        'frontchannel_logout_supported': True,
        'end_session_endpoint': 'https://login.microsoftonline.com/vibber_tenant/oauth2/v2.0/logout',
        'claims_supported': [
            'sub',
            'iss',
            'cloud_instance_name',
            'cloud_instance_host_name',
            'cloud_graph_host_name',
            'msgraph_host',
            'aud',
            'exp',
            'iat',
            'auth_time',
            'acr',
            'nonce',
            'preferred_username',
            'name',
            'tid',
            'ver',
            'at_hash',
            'c_hash',
            'email',
        ],
        'kerberos_endpoint': 'https://login.microsoftonline.com/vibber_tenant/kerberos',
        'tenant_region_scope': 'EU',
        'cloud_instance_name': 'microsoftonline.com',
        'cloud_graph_host_name': 'graph.windows.net',
        'msgraph_host': 'graph.microsoft.com',
        'rbac_url': 'https://pas.windows.net',
    }


def openid_config_url(multi_tenant=False) -> str:
    if multi_tenant:
        return 'https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration'
    return 'https://login.microsoftonline.com/vibber_tenant_id/v2.0/.well-known/openid-configuration'


def keys_url() -> str:
    return 'https://login.microsoftonline.com/vibber_tenant/discovery/v2.0/keys'


signing_key_a = generate_private_key()
signing_key_b = generate_private_key()
