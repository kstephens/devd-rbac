from typing import Iterable
from dataclasses import dataclass

Username = str
Password = str


@dataclass
class UserPass:
    username: Username
    password: Password


UserPasses = Iterable[UserPass]


@dataclass
class Token:
    value: str


CookieName = str
CookieValue = str


@dataclass
class Cookie:
    name: CookieName
    value: CookieValue


Tokens = Iterable[Token]

Credential = UserPass | Token | Cookie
