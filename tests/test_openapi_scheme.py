import fastapi
import openapi_spec_validator
import pydantic
import pytest
from demo_project.main import app
from fastapi.testclient import TestClient
from packaging import version

openapi_schema = {
    'openapi': '3.1.0',
    'info': {
        'title': 'My Project',
        'description': '## Welcome to my API! \n This is my description, written in `markdown`',
        'version': '1.0.0',
    },
    'paths': {
        '/api/v1/hello': {
            'get': {
                'tags': ['hello'],
                'summary': 'Say hello',
                'description': 'Wonder who we say hello to?',
                'operationId': 'helloWorld',
                'responses': {
                    '200': {
                        'description': 'Successful Response',
                        'content': {
                            'application/json': {'schema': {'$ref': '#/components/schemas/HelloWorldResponse'}}
                        },
                    }
                },
                'security': [{'AzureAD_PKCE_single_tenant': ['user_impersonation']}],
            }
        },
        '/api/v1/hello-multi-auth': {
            'get': {
                'tags': ['hello'],
                'summary': 'Say hello with an API key',
                'description': 'Wonder how this auth is done?',
                'operationId': 'helloWorldApiKeyMultiAuth',
                'responses': {
                    '200': {
                        'description': 'Successful Response',
                        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/TokenType'}}},
                    }
                },
                'security': [{'AzureAD_PKCE_multi_tenant': []}, {'APIKeyHeader': []}],
            }
        },
        '/api/v1/hello-multi-auth-b2c': {
            'get': {
                'tags': ['hello'],
                'summary': 'Say hello with an API key',
                'description': 'Wonder how this auth is done?',
                'operationId': 'helloWorldApiKeyMultiAuthB2C',
                'responses': {
                    '200': {
                        'description': 'Successful Response',
                        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/TokenType'}}},
                    }
                },
                'security': [{'AzureAD_PKCE_B2C_multi_tenant': []}, {'APIKeyHeader': []}],
            }
        },
        '/api/v1/hello-graph': {
            'get': {
                'tags': ['graph'],
                'summary': 'Fetch graph API using OBO',
                'description': 'An example on how to use "on behalf of"-flow to fetch a graph token and then fetch data from graph.',
                'operationId': 'helloGraph',
                'responses': {
                    '200': {
                        'description': 'Successful Response',
                        'content': {'application/json': {'schema': {'title': 'Response Hellograph'}}},
                    }
                },
                'security': [{'AzureAD_PKCE_single_tenant': []}],
            }
        },
    },
    'components': {
        'schemas': {
            'HelloWorldResponse': {
                'properties': {
                    'hello': {'type': 'string', 'title': 'Hello', 'description': "What we're saying hello to"},
                    'user': {'$ref': '#/components/schemas/User', 'description': 'The user object'},
                },
                'type': 'object',
                'required': ['hello', 'user'],
                'title': 'HelloWorldResponse',
            },
            'TokenType': {
                'properties': {
                    'api_key': {'type': 'boolean', 'title': 'Api Key', 'description': 'API key was used'},
                    'azure_auth': {'type': 'boolean', 'title': 'Azure Auth', 'description': 'Azure auth was used'},
                },
                'type': 'object',
                'required': ['api_key', 'azure_auth'],
                'title': 'TokenType',
            },
            'User': {
                'properties': {
                    'aud': {
                        'type': 'string',
                        'title': 'Aud',
                        'description': 'Identifies the intended audience of the token. In v2.0 tokens, this value is always the client ID of the API. In v1.0 tokens, it can be the client ID or the resource URI used in the request.',
                    },
                    'iss': {
                        'type': 'string',
                        'title': 'Iss',
                        'description': 'Identifies the STS that constructs and returns the token, and the Azure Entra ID tenant of the authenticated user. If the token issued is a v2.0 token (see the ver claim), the URI ends in /v2.0.',
                    },
                    'idp': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Idp',
                        'description': 'Records the identity provider that authenticated the subject of the token. This value is identical to the value of the Issuer claim unless the user account is not in the same tenant as the issuer, such as guests. Use the value of iss if the claim is not present.',
                    },
                    'iat': {
                        'type': 'integer',
                        'title': 'Iat',
                        'description': 'Specifies when the authentication for this token occurred.',
                    },
                    'nbf': {
                        'type': 'integer',
                        'title': 'Nbf',
                        'description': 'Specifies the time after which the JWT can be processed.',
                    },
                    'exp': {
                        'type': 'integer',
                        'title': 'Exp',
                        'description': 'Specifies the expiration time before which the JWT can be accepted for processing.',
                    },
                    'aio': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Aio',
                        'description': 'An internal claim used by Azure Entra ID to record data for token reuse. Resources should not use this claim.',
                    },
                    'name': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Name',
                        'description': 'Provides a human-readable value that identifies the subject of the token.',
                    },
                    'scp': {
                        'items': {'type': 'string'},
                        'type': 'array',
                        'title': 'Scp',
                        'description': 'The set of scopes exposed by the application for which the client application has requested (and received) consent. Only included for user tokens.',
                        'default': [],
                    },
                    'roles': {
                        'items': {'type': 'string'},
                        'type': 'array',
                        'title': 'Roles',
                        'description': 'The set of permissions exposed by the application that the requesting application or user has been given permission to call.',
                        'default': [],
                    },
                    'wids': {
                        'items': {'type': 'string'},
                        'type': 'array',
                        'title': 'Wids',
                        'description': 'Denotes the tenant-wide roles assigned to this user, from the section of roles present in Azure Entra ID built-in roles.',
                        'default': [],
                    },
                    'groups': {
                        'items': {'type': 'string'},
                        'type': 'array',
                        'title': 'Groups',
                        'description': 'Provides object IDs that represent the group memberships of the subject.',
                        'default': [],
                    },
                    'sub': {
                        'type': 'string',
                        'title': 'Sub',
                        'description': 'The principal associated with the token.',
                    },
                    'oid': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Oid',
                        'description': 'The immutable identifier for the requestor, which is the verified identity of the user or service principal',
                    },
                    'tid': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Tid',
                        'description': 'Represents the tenant that the user is signing in to',
                    },
                    'uti': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Uti',
                        'description': 'Token identifier claim, equivalent to jti in the JWT specification. Unique, per-token identifier that is case-sensitive.',
                    },
                    'rh': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Rh',
                        'description': 'Token identifier claim, equivalent to jti in the JWT specification. Unique, per-token identifier that is case-sensitive.',
                    },
                    'ver': {
                        'type': 'string',
                        'enum': ['1.0', '2.0'],
                        'title': 'Ver',
                        'description': 'Indicates the version of the access token.',
                    },
                    'acct': {
                        'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                        'title': 'Acct',
                        'description': "User's account status in tenant",
                    },
                    'auth_time': {
                        'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                        'title': 'Auth Time',
                        'description': 'Time when the user last authenticated; See OpenID Connect spec',
                    },
                    'ctry': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Ctry',
                        'description': "User's country/region",
                    },
                    'email': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Email',
                        'description': 'The addressable email for this user, if the user has one',
                    },
                    'family_name': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Family Name',
                        'description': 'Provides the last name, surname, or family name of the user as defined in the user object',
                    },
                    'fwd': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Fwd',
                        'description': 'IP address',
                    },
                    'given_name': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Given Name',
                        'description': 'Provides the first or "given" name of the user, as set on the user object',
                    },
                    'idtyp': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Idtyp',
                        'description': 'Signals whether the token is an app-only token',
                    },
                    'in_corp': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'In Corp',
                        'description': 'Signals if the client is logging in from the corporate network; if they are not, the claim is not included',
                    },
                    'ipaddr': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Ipaddr',
                        'description': 'The IP address the user authenticated from.',
                    },
                    'login_hint': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Login Hint',
                        'description': 'Login hint',
                    },
                    'onprem_sid': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Onprem Sid',
                        'description': 'On-premises security identifier',
                    },
                    'pwd_exp': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Pwd Exp',
                        'description': 'The datetime at which the password expires',
                    },
                    'pwd_url': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Pwd Url',
                        'description': 'A URL that the user can visit to change their password',
                    },
                    'sid': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Sid',
                        'description': 'Session ID, used for per-session user sign out',
                    },
                    'tenant_ctry': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Tenant Ctry',
                        'description': "Resource tenant's country/region",
                    },
                    'tenant_region_scope': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Tenant Region Scope',
                        'description': 'Region of the resource tenant',
                    },
                    'upn': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Upn',
                        'description': 'An identifier for the user that can be used with the username_hint parameter; not a durable identifier for the user and should not be used to key data',
                    },
                    'verified_primary_email': {
                        'items': {'type': 'string'},
                        'type': 'array',
                        'title': 'Verified Primary Email',
                        'description': "Sourced from the user's PrimaryAuthoritativeEmail",
                        'default': [],
                    },
                    'verified_secondary_email': {
                        'items': {'type': 'string'},
                        'type': 'array',
                        'title': 'Verified Secondary Email',
                        'description': "Sourced from the user's SecondaryAuthoritativeEmail",
                        'default': [],
                    },
                    'vnet': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Vnet',
                        'description': 'VNET specifier information',
                    },
                    'xms_pdl': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Xms Pdl',
                        'description': 'Preferred data location',
                    },
                    'xms_pl': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Xms Pl',
                        'description': 'User-preferred language',
                    },
                    'xms_tpl': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Xms Tpl',
                        'description': 'Tenant-preferred language',
                    },
                    'ztdid': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Ztdid',
                        'description': 'Zero-touch Deployment ID',
                    },
                    'acr': {
                        'anyOf': [{'type': 'string', 'enum': ['0', '1']}, {'type': 'null'}],
                        'title': 'Acr',
                        'description': 'A value of 0 for the "Authentication context class" claim indicates the end-user authentication did not meet the requirements of ISO/IEC 29115. Only available in V1.0 tokens',
                    },
                    'amr': {
                        'items': {'type': 'string'},
                        'type': 'array',
                        'title': 'Amr',
                        'description': 'Identifies the authentication method of the subject of the token. Only available in V1.0 tokens',
                        'default': [],
                    },
                    'appid': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Appid',
                        'description': 'The application ID of the client using the token. Only available in V1.0 tokens',
                    },
                    'appidacr': {
                        'anyOf': [{'type': 'string', 'enum': ['0', '1', '2']}, {'type': 'null'}],
                        'title': 'Appidacr',
                        'description': 'Indicates authentication method of the client. Only available in V1.0 tokens',
                    },
                    'unique_name': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Unique Name',
                        'description': 'Provides a human readable value that identifies the subject of the token. Only available in V1.0 tokens',
                    },
                    'azp': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Azp',
                        'description': 'The application ID of the client using the token. Only available in V2.0 tokens',
                    },
                    'azpacr': {
                        'anyOf': [{'type': 'string', 'enum': ['0', '1', '2']}, {'type': 'null'}],
                        'title': 'Azpacr',
                        'description': 'Indicates the authentication method of the client. Only available in V2.0 tokens',
                    },
                    'preferred_username': {
                        'anyOf': [{'type': 'string'}, {'type': 'null'}],
                        'title': 'Preferred Username',
                        'description': 'The primary username that represents the user. Only available in V2.0 tokens',
                    },
                    'claims': {
                        'additionalProperties': True,
                        'type': 'object',
                        'title': 'Claims',
                        'description': 'The entire decoded token',
                    },
                    'access_token': {
                        'type': 'string',
                        'title': 'Access Token',
                        'description': 'The access_token. Can be used for fetching the Graph API',
                    },
                    'is_guest': {
                        'type': 'boolean',
                        'title': 'Is Guest',
                        'description': 'The user is a guest user in the tenant',
                        'default': False,
                    },
                },
                'type': 'object',
                'required': ['aud', 'iss', 'iat', 'nbf', 'exp', 'sub', 'ver', 'claims', 'access_token'],
                'title': 'User',
            },
        },
        'securitySchemes': {
            'AzureAD_PKCE_single_tenant': {
                'type': 'oauth2',
                'description': '`Leave client_secret blank`',
                'flows': {
                    'authorizationCode': {
                        'scopes': {
                            'api://oauth299-9999-9999-abcd-efghijkl1234567890/user_impersonation': '**No client secret needed, leave blank**'
                        },
                        'authorizationUrl': 'https://login.microsoftonline.com/vibber_tenant_id/oauth2/v2.0/authorize',
                        'tokenUrl': 'https://login.microsoftonline.com/vibber_tenant_id/oauth2/v2.0/token',
                    }
                },
            },
            'AzureAD_PKCE_multi_tenant': {
                'type': 'oauth2',
                'description': '`Leave client_secret blank`',
                'flows': {
                    'authorizationCode': {
                        'scopes': {
                            'api://oauth299-9999-9999-abcd-efghijkl1234567890/user_impersonation': 'User impersonation'
                        },
                        'authorizationUrl': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                        'tokenUrl': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                    }
                },
            },
            'APIKeyHeader': {'type': 'apiKey', 'in': 'header', 'name': 'TEST-API-KEY'},
            'AzureAD_PKCE_B2C_multi_tenant': {
                'type': 'oauth2',
                'description': '`Leave client_secret blank`',
                'flows': {
                    'authorizationCode': {
                        'scopes': {
                            'api://oauth299-9999-9999-abcd-efghijkl1234567890/user_impersonation': 'User impersonation'
                        },
                        'authorizationUrl': 'https://dummy.com/',
                        'tokenUrl': 'https://dummy.com/',
                    }
                },
            },
        },
    },
}


@pytest.fixture
def test_client():
    """
    Test client that does not run startup event.
    All these tests fails before we get to loading the OpenID Connect configuration.
    """
    yield TestClient(app=app)


@pytest.mark.skipif(
    version.parse(fastapi.__version__) < version.parse('0.138.0'),
    reason='OpenAPI schema (security scopes) differs on older FastAPI versions',
)
@pytest.mark.skipif(
    version.parse(pydantic.__version__) < version.parse('2.6.2'), reason='Different schema with older pydantic version'
)
def test_openapi_schema(test_client):
    response = test_client.get('api/v1/openapi.json')
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_validate_openapi_spec(test_client):
    response = test_client.get('api/v1/openapi.json')
    assert response.status_code == 200, response.text
    openapi_spec_validator.validate_spec(response.json())


def test_no_token(test_client):
    response = test_client.get('/api/v1/hello')
    assert response.status_code == 401, response.text
    assert response.json() == {'detail': 'Not authenticated'}


def test_incorrect_token(test_client):
    response = test_client.get('/api/v1/hello', headers={'Authorization': 'Non-existent testtoken'})
    assert response.status_code == 401, response.text
    assert response.json() == {'detail': 'Not authenticated'}


def test_token(test_client):
    response = test_client.get('/api/v1/hello', headers={'Authorization': 'Bearer '})
    assert response.status_code == 401, response.text
    assert response.json() == {'detail': {'error': 'invalid_token', 'message': 'Invalid token format'}}
