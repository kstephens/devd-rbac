from typing import cast
import logging
import re
import time
import base64
from dataclasses import dataclass
from .cipher import Cipher
from .credential import BearerToken, UserPass, Cookie
from .domain import SubjectDomain, PasswordDomain


@dataclass
class AuthTokenRequest:
    userpass: UserPass
    description: str
    lifetime: int | None


class Authenticator:
    subject_domain: SubjectDomain
    password_domain: PasswordDomain
    cipher_key: str
    cookie_name: str

    def __init__(
        self,
        subject_domain: SubjectDomain,
        password_domain: PasswordDomain,
        cipher_key: str,
        cookie_name: str,
    ):
        self.subject_domain, self.password_domain = subject_domain, password_domain
        self.cipher_key, self.cookie_name = cipher_key, cookie_name
        self.clock = time.time

    def authenticate(
        self,
        userpass: UserPass | None,
        auth: str | None,
        cookie: str | None,
    ) -> UserPass | None:
        """
        Authenticate by one of the following, in order of precedence:
        - Raw username and password
        - HTTP Basic Auth header
        - HTTP Authorization: Bearer token
        - HTTP Cookie
        """
        result = None
        if userpass is not None and not result:
            result = self.auth_userpass(userpass)

        if auth is not None and not result:
            userpass = self.parse_basic(auth)
            if userpass is not None:
                return self.auth_userpass(userpass)
            if not result:
                token = self.parse_bearer(auth)
                if token is not None:
                    return self.auth_token(token)

        if cookie is not None and not result:
            result = self.auth_cookie(Cookie(self.cookie_name, cookie))
        return result

    def auth_userpass(self, userpass: UserPass) -> UserPass | None:
        """Verify username and password."""
        logging.debug("%s", f"auth_userpass: {userpass.username=}")
        if not (user := self.subject_domain.user_by_name(userpass.username)):
            return None
        logging.debug("%s", f"auth_userpass: {user=}")
        if not (password := self.password_domain.password_for_user(user)):
            return None
        matches = (
            password.username == userpass.username
            and password.password == userpass.password
        )
        logging.debug("%s", f"auth_userpass: {password.username=} {matches=}")
        if matches:
            return userpass
        return None

    def auth_cookie(self, cookie: Cookie) -> UserPass | None:
        """Decode a cookie"""
        return self.secret_to_userpass(cookie.value)

    def auth_token(self, token: BearerToken) -> UserPass | None:
        """Decode a Bearer token"""
        return self.secret_to_userpass(token.value)

    ###################################################

    def auth_request_cookie(self, auth_request: AuthTokenRequest) -> Cookie:
        """Return a new Cookie token."""
        return Cookie(self.cookie_name, self.auth_request_to_secret(auth_request))

    def auth_request_token(self, auth_request: AuthTokenRequest) -> BearerToken:
        """Return a new Bearer token."""
        return BearerToken(
            self.auth_request_to_secret(auth_request), auth_request.description
        )

    ###################################################

    def auth_request_to_secret(self, auth_request: AuthTokenRequest) -> str:
        logging.debug("userpass_to_secret %s", f"{auth_request.userpass.username=}")
        cipher = Cipher(self.cipher_key)
        issued = int(self.clock())
        if auth_request.lifetime:
            expiry = int(issued + auth_request.lifetime)
        else:
            expiry = 0
        logging.info(
            "userpass_to_secret %s",
            f"{auth_request.userpass.username=} {issued=} {auth_request.lifetime=} {expiry=}",
        )
        plaintext = f"5:{auth_request.userpass.username}:{issued}:{auth_request.lifetime}:{expiry}:{auth_request.userpass.password}"
        return cast(str, cipher.encipher(plaintext))

    def secret_to_userpass(self, secret: str) -> UserPass | None:
        logging.info("secret_to_userpass %s", f"{secret=}")
        cipher = Cipher(self.cipher_key)
        secret = cast(str, cipher.decipher(secret))
        try:
            n_fields, username, issued_s, lifetime_s, expiry_s, password = secret.split(
                ":", 5
            )
            assert n_fields == "5"
            issued = int(issued_s)
            lifetime = int(lifetime_s)
            expiry = int(expiry_s)
        # pylint: disable-next=bare-except
        except:
            return None
        if expiry and lifetime and self.clock() >= expiry:
            logging.info(
                "secret_to_userpass %s",
                f"expired {username=} {issued=} {lifetime=} {expiry=}",
            )
            return None
        return UserPass(username, password)

    ###################################################

    def parse_basic(self, auth_header: str) -> UserPass | None:
        if m := re.match(r"^Basic +(\S+)$", auth_header):
            basic_auth = base64.b64decode(m[1]).decode()
            username, password = basic_auth.split(":", 1)
            logging.debug("%s", f"parse_basic: {username=}")
            return UserPass(username, password)
        return None

    def parse_bearer(self, auth_header: str) -> BearerToken | None:
        if m := re.match(r"^Bearer +(\S+)$", auth_header):
            token = m[1]
            logging.debug("%s", f"parse_bearer {token=}")
            return BearerToken(token, "")
        return None
