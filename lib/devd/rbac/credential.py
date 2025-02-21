from typing import Iterable
from dataclasses import dataclass

Username = str
Password = str
CookieName = str
CookieValue = str


@dataclass
class UserPass:
    username: Username
    password: Password


@dataclass
class BearerToken:
    value: str
    description: str


@dataclass
class Cookie:
    name: CookieName
    value: CookieValue


UserPasses = Iterable[UserPass]
BearerTokens = Iterable[BearerToken]
Credential = UserPass | BearerToken | Cookie
