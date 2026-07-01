<h1 align="center">
  <img margin="0 10px 0 0" src="https://raw.githubusercontent.com/vibber-ai/fastapi-azure-auth/main/docs/static/img/global/fastad.png" width="124px"/><br/>
  FastAPI-Azure-Auth
</h1>

<p align="center">
    <em>Azure Entra ID Authentication for FastAPI apps made easy.</em>
</p>
<p align="center">
    <!-- Line 1 -->
    <a href="https://python.org">
        <img src="https://img.shields.io/badge/python-v3.8+-blue.svg?logo=python&logoColor=white&label=python" alt="Python version">
    </a>
    <a href="https://fastapi.tiangolo.com/">
        <img src="https://img.shields.io/badge/FastAPI-0.68.0+%20-blue.svg?logo=fastapi&logoColor=white&label=fastapi" alt="FastAPI Version">
    </a>
    <a href="https://pypi.org/pypi/fastapi-azure-auth">
        <img src="https://img.shields.io/pypi/v/fastapi-azure-auth.svg?logo=pypi&logoColor=white&label=pypi" alt="Package version">
    </a>
    <!-- Line 2 -->
    <br/>
    <a href="https://codecov.io/gh/vibber-ai/fastapi-azure-auth">
        <img src="https://codecov.io/gh/vibber-ai/fastapi-azure-auth/branch/main/graph/badge.svg?token=BTFGII4GYR" alt="Codecov">
    </a>
    <a href="https://github.com/pre-commit/pre-commit">
        <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="Pre-commit">
    </a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Black">
    </a>
    <a href="http://mypy-lang.org">
        <img src="http://www.mypy-lang.org/static/mypy_badge.svg" alt="mypy">
    </a>
    <a href="https://pycqa.github.io/isort/">
        <img src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336" alt="isort">
    </a>
    <!-- Line 3 -->
    <br/>
    <a href="https://docs.microsoft.com/en-us/azure/active-directory/develop/single-and-multi-tenant-apps">
        <img src="https://img.shields.io/badge/Single--tenant-Supported-blue?logo=Microsoft%20Azure&logoColor=white">
    </a>
    <a href="https://docs.microsoft.com/en-us/azure/active-directory/develop/single-and-multi-tenant-apps">
        <img src="https://img.shields.io/badge/Multi--tenant-Supported-blue?logo=Microsoft%20Azure&logoColor=white">
    </a>
    <a href="https://learn.microsoft.com/en-us/azure/active-directory-b2c/overview">
        <img src="https://img.shields.io/badge/B2C-Supported-blue?logo=Microsoft%20Azure&logoColor=white">
    </a>
</p>


## 🚀 Description

> FastAPI is a modern, fast (high-performance), web framework for building APIs with Python, based on standard Python type hints.

Vibber is the control plane for enterprise AI. The single place to build, run and manage AI agents. Production-ready in minutes, not months. This package enables our developers (and you 😊) to create features without worrying about authentication and authorization.

Also, [contact us!](mailto:jonas@vibber.ai)

## 📚 Resources

The [documentation](https://vibber-ai.github.io/fastapi-azure-auth/) contains a full tutorial on how to configure Azure Entra ID
and FastAPI for single- and multi-tenant applications as well as B2C apps. It includes examples on how to lock down
your APIs to certain scopes, tenants, roles etc. For first time users it's strongly advised to set up your
application exactly how it's described there, and then alter it to your needs later.

[**MIT License**](https://github.com/vibber-ai/fastapi-azure-auth/blob/main/LICENSE)
| [**Documentation**](https://vibber-ai.github.io/fastapi-azure-auth/)
| [**GitHub**](https://github.com/snok/django-guid)


## ⚡ Setup

This is a tl;dr intended to give you an idea of what this package does and how to use it.
For a more in-depth tutorial and settings reference you should read the
[documentation](https://vibber-ai.github.io/fastapi-azure-auth/).


#### 1. Install this library:
```bash
pip install fastapi-azure-auth
# or
poetry add fastapi-azure-auth
```

#### 2. Configure your FastAPI app
Include `swagger_ui_oauth2_redirect_url` and `swagger_ui_init_oauth` in your FastAPI app initialization:

```python
# file: main.py
app = FastAPI(
    ...
    swagger_ui_oauth2_redirect_url='/oauth2-redirect',
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': settings.OPENAPI_CLIENT_ID,
    },
)
```

#### 3. Setup CORS
Ensure you have CORS enabled for your local environment, such as `http://localhost:8000`.

#### 4. Configure FastAPI-Azure-Auth
Configure either [`SingleTenantAzureAuthorizationCodeBearer`](https://vibber-ai.github.io/fastapi-azure-auth/settings/single_tenant), [`MultiTenantAzureAuthorizationCodeBearer`](https://vibber-ai.github.io/fastapi-azure-auth/settings/multi_tenant) or [`B2CMultiTenantAuthorizationCodeBearer`](https://vibber-ai.github.io/fastapi-azure-auth/settings/b2c)


```python
# file: demoproj/api/dependencies.py
from fastapi_azure_auth.auth import SingleTenantAzureAuthorizationCodeBearer

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes={
        f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user_impersonation',
    }
)
```
or for multi-tenant applications:
```python
# file: demoproj/api/dependencies.py
from fastapi_azure_auth.auth import MultiTenantAzureAuthorizationCodeBearer

azure_scheme = MultiTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    scopes={
        f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user_impersonation',
    },
    validate_iss=False
)
```
To validate the `iss`, configure an
[`iss_callable`](https://vibber-ai.github.io/fastapi-azure-auth/multi-tenant/accept_specific_tenants_only).

#### 5. Configure dependencies

Add `azure_scheme` as a dependency for your views/routers, using either `Security()` or `Depends()`.
```python
# file: main.py
from demoproj.api.dependencies import azure_scheme

app.include_router(api_router, prefix=settings.API_V1_STR, dependencies=[Security(azure_scheme, scopes=['user_impersonation'])])
```

#### 6. Load config on startup

Optional but recommended.

```python
# file: main.py
@app.on_event('startup')
async def load_config() -> None:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()
```


## 📄 Example OpenAPI documentation
Your OpenAPI documentation will get an `Authorize` button, which can be used to authenticate.
![authorize](docs/static/img/single-and-multi-tenant/fastapi_1_authorize_button.png)

The user can select which scopes to authenticate with, based on your configuration.
![scopes](docs/static/img/single-and-multi-tenant/fastapi_3_authenticate.png)
