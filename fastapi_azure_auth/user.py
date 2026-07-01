from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Claims(BaseModel):
    """
    A more complete overview of the claims available in an access token can be found here:
    https://learn.microsoft.com/en-us/azure/active-directory/develop/access-tokens#payload-claims
    """

    aud: str = Field(
        ...,
        description='Identifies the intended audience of the token. In v2.0 tokens, this value is always the client ID'
        ' of the API. In v1.0 tokens, it can be the client ID or the resource URI used in the request.',
    )
    iss: str = Field(
        ...,
        description='Identifies the STS that constructs and returns the token, and the Azure Entra ID tenant of the'
        ' authenticated user. If the token issued is a v2.0 token (see the ver claim), the URI ends in /v2.0.',
    )
    idp: str | None = Field(
        default=None,
        description='Records the identity provider that authenticated the subject of the token. This value is identical'
        ' to the value of the Issuer claim unless the user account is not in the same tenant as the issuer, such as'
        ' guests. Use the value of iss if the claim is not present.',
    )
    iat: int = Field(
        ...,
        description='Specifies when the authentication for this token occurred.',
    )
    nbf: int = Field(
        ...,
        description='Specifies the time after which the JWT can be processed.',
    )
    exp: int = Field(
        ...,
        description='Specifies the expiration time before which the JWT can be accepted for processing.',
    )
    aio: str | None = Field(
        default=None,
        description='An internal claim used by Azure Entra ID to record data for token reuse. Resources should not use this claim.',
    )
    name: str | None = Field(
        default=None,
        description='Provides a human-readable value that identifies the subject of the token.',
    )
    scp: list[str] = Field(
        default=[],
        description='The set of scopes exposed by the application for which the client application has requested (and received) consent. Only included for user tokens.',
    )
    roles: list[str] = Field(
        default=[],
        description='The set of permissions exposed by the application that the requesting application or user has been given permission to call.',
    )
    wids: list[str] = Field(
        default=[],
        description='Denotes the tenant-wide roles assigned to this user, from the section of roles present in Azure Entra ID built-in roles.',
    )
    groups: list[str] = Field(
        default=[],
        description='Provides object IDs that represent the group memberships of the subject.',
    )
    sub: str = Field(
        ...,
        description='The principal associated with the token.',
    )
    oid: str | None = Field(
        default=None,
        description='The immutable identifier for the requestor, which is the verified identity of the user or service principal',
    )
    tid: str | None = Field(
        default=None,
        description='Represents the tenant that the user is signing in to',
    )
    uti: str | None = Field(
        default=None,
        description='Token identifier claim, equivalent to jti in the JWT specification. Unique, per-token identifier that is case-sensitive.',
    )
    rh: str | None = Field(
        default=None,
        description='Token identifier claim, equivalent to jti in the JWT specification. Unique, per-token identifier that is case-sensitive.',
    )
    ver: Literal['1.0', '2.0'] = Field(
        ...,
        description='Indicates the version of the access token.',
    )

    # Optional claims, configured in Azure Entra ID
    acct: int | None = Field(
        default=None,
        description="User's account status in tenant",
    )
    auth_time: int | None = Field(
        default=None,
        description='Time when the user last authenticated; See OpenID Connect spec',
    )
    ctry: str | None = Field(
        default=None,
        description="User's country/region",
    )
    email: str | None = Field(
        default=None,
        description='The addressable email for this user, if the user has one',
    )
    family_name: str | None = Field(
        default=None,
        description='Provides the last name, surname, or family name of the user as defined in the user object',
    )
    fwd: str | None = Field(
        default=None,
        description='IP address',
    )
    given_name: str | None = Field(
        default=None,
        description='Provides the first or "given" name of the user, as set on the user object',
    )
    idtyp: str | None = Field(
        default=None,
        description='Signals whether the token is an app-only token',
    )
    in_corp: str | None = Field(
        default=None,
        description='Signals if the client is logging in from the corporate network; if they are not, the claim is not included',
    )
    ipaddr: str | None = Field(
        default=None,
        description='The IP address the user authenticated from.',
    )
    login_hint: str | None = Field(
        default=None,
        description='Login hint',
    )
    onprem_sid: str | None = Field(
        default=None,
        description='On-premises security identifier',
    )
    pwd_exp: str | None = Field(
        default=None,
        description='The datetime at which the password expires',
    )
    pwd_url: str | None = Field(
        default=None,
        description='A URL that the user can visit to change their password',
    )
    sid: str | None = Field(
        default=None,
        description='Session ID, used for per-session user sign out',
    )
    tenant_ctry: str | None = Field(
        default=None,
        description="Resource tenant's country/region",
    )
    tenant_region_scope: str | None = Field(
        default=None,
        description='Region of the resource tenant',
    )
    upn: str | None = Field(
        default=None,
        description='An identifier for the user that can be used with the username_hint parameter; not a durable identifier for the user and should not be used to key data',
    )
    verified_primary_email: list[str] = Field(
        default=[],
        description="Sourced from the user's PrimaryAuthoritativeEmail",
    )
    verified_secondary_email: list[str] = Field(
        default=[],
        description="Sourced from the user's SecondaryAuthoritativeEmail",
    )
    vnet: str | None = Field(
        default=None,
        description='VNET specifier information',
    )
    xms_pdl: str | None = Field(
        default=None,
        description='Preferred data location',
    )
    xms_pl: str | None = Field(
        default=None,
        description='User-preferred language',
    )
    xms_tpl: str | None = Field(
        default=None,
        description='Tenant-preferred language',
    )
    ztdid: str | None = Field(
        default=None,
        description='Zero-touch Deployment ID',
    )

    # V1.0 only
    acr: Literal['0', '1'] | None = Field(
        default=None,
        description='A value of 0 for the "Authentication context class" claim indicates the end-user authentication '
        'did not meet the requirements of ISO/IEC 29115. Only available in V1.0 tokens',
    )
    # V1.0 only
    amr: list[str] = Field(
        default=[],
        description='Identifies the authentication method of the subject of the token. Only available in V1.0 tokens',
    )
    # V1.0 only
    appid: str | None = Field(
        default=None,
        description='The application ID of the client using the token. Only available in V1.0 tokens',
    )
    # V1.0 only
    appidacr: Literal['0', '1', '2'] | None = Field(
        default=None,
        description='Indicates authentication method of the client. Only available in V1.0 tokens',
    )
    # V1.0 only
    unique_name: str | None = Field(
        default=None,
        description='Provides a human readable value that identifies the subject of the token. Only available in V1.0 tokens',
    )

    # V2.0 only
    azp: str | None = Field(
        default=None,
        description='The application ID of the client using the token. Only available in V2.0 tokens',
    )
    # V2.0 only
    azpacr: Literal['0', '1', '2'] | None = Field(
        default=None,
        description='Indicates the authentication method of the client. Only available in V2.0 tokens',
    )
    # V2.0 only
    preferred_username: str | None = Field(
        default=None,
        description='The primary username that represents the user. Only available in V2.0 tokens',
    )

    @field_validator('scp', mode='before')
    def scopes_to_list(cls, v: object) -> object:
        """
        Validator on the scope attribute that convert the space separated list
        of scope into an actual list of scope.
        """
        return v.split(' ') if isinstance(v, str) else v


class User(Claims):
    claims: dict[str, Any] = Field(
        ...,
        description='The entire decoded token',
    )
    access_token: str = Field(
        ...,
        description='The access_token. Can be used for fetching the Graph API',
    )
    is_guest: bool = Field(
        False,
        description='The user is a guest user in the tenant',
    )
