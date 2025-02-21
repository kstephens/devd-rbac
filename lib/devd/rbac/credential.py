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
class Token:
    value: str


@dataclass
class Cookie:
    name: CookieName
    value: CookieValue


UserPasses = Iterable[UserPass]
Tokens = Iterable[Token]
Credential = UserPass | Token | Cookie
