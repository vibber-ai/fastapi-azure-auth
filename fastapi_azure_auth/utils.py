from typing import Any

import jwt


def is_guest(claims: dict[str, Any]) -> bool:
    """
    Check if the user is a guest user
    """
    # if the user has set up `acct` claim in Azure, that's most efficient. 0 = tenant member, 1 = guest
    if claims.get('acct') == 1:
        return True
    # formula: idp exist and idp != iss: guest user
    claims_iss: str = claims.get('iss', '')
    idp: str = claims.get('idp', claims_iss)
    return idp != claims_iss


def get_unverified_header(access_token: str) -> dict[str, Any]:
    """
    Get header from the access token without verifying the signature
    """
    return dict(jwt.get_unverified_header(access_token))


def get_unverified_claims(access_token: str) -> dict[str, Any]:
    """
    Get claims from the access token without verifying the signature
    """
    return dict(jwt.decode(access_token, options={'verify_signature': False}))
