from typing import Any

import httpx2
import jwt
from fastapi import APIRouter, Depends, Request
from httpx2 import AsyncClient

from demo_project.api.dependencies import azure_scheme
from demo_project.core.config import settings

router = APIRouter()


@router.get(
    '/hello-graph',
    summary='Fetch graph API using OBO',
    name='graph',
    operation_id='helloGraph',
    dependencies=[Depends(azure_scheme)],
)
async def graph_world(request: Request) -> Any:  # noqa: ANN401
    """
    An example on how to use "on behalf of"-flow to fetch a graph token and then fetch data from graph.
    """
    async with AsyncClient() as client:
        # Use the users access token and fetch a new access token for the Graph API
        obo_response: httpx2.Response = await client.post(
            f'https://login.microsoftonline.com/{settings.TENANT_ID}/oauth2/v2.0/token',
            data={
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'client_id': settings.APP_CLIENT_ID,
                'client_secret': settings.GRAPH_SECRET,
                'assertion': request.state.user.access_token,
                'scope': 'https://graph.microsoft.com/user.read',
                'requested_token_use': 'on_behalf_of',
            },
        )

        if obo_response.is_success:
            # Call the graph `/me` endpoint to fetch more information about the current user, using the new token
            graph_response: httpx2.Response = await client.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {obo_response.json()["access_token"]}'},
            )
            graph = graph_response.json()
        else:
            graph = 'skipped'

        # Return all the information to the end user
        return (
            {'claims': jwt.decode(request.state.user.access_token, options={'verify_signature': False})}
            | {'obo_response': obo_response.json()}
            | {'graph_response': graph}
        )
