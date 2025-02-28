from typing import Any, Iterable, Dict, Tuple, Callable
from pathlib import Path
import logging
import os
import re
import json
from datetime import datetime, timezone
from dataclasses import dataclass
import tabulate
from .loader import DomainFileLoader
from .credential import UserPass, Cookie, BearerToken
from .auth import Authenticator, AuthTokenRequest
from ..rbac import (
    Domain,
    Solver,
    Request,
    Permission,
    Action,
    Resource,
    Rule,
    Role,
)


@dataclass
class AuthRequest:
    header: str | None
    cookie: str | None


@dataclass
class ResourceRequest:
    action: str
    resource: str
    auth_request: AuthRequest  #  | None
    body: bytes


ResourceResponse = Tuple[int, dict, bytes]


class App:
    authenticator: Authenticator

    def __init__(self, resource_root: str, domain_root: str):
        self.verbose = False
        self.resource_root = Path(resource_root)
        self.domain_root = Path(domain_root)
        self.environ: Dict[str, str] = {}
        self.start_response = None
        self.auth_cookie_name = "authsession"
        self.cipher_key = "123"
        self.authenticator = self.make_authenticator()
        self.default_cookie_lifetime = 60

    ######################################

    def login(self, request: UserPass) -> Cookie | None:
        userpass = self.authenticator.auth_userpass(request)
        logging.info("%s", f"login: {request.username=}")
        if userpass:
            auth_request = AuthTokenRequest(
                userpass,
                "login",
                self.default_cookie_lifetime,
            )
            return self.authenticator.auth_request_cookie(auth_request)
        return None

    def auth_token(self, auth_request: AuthTokenRequest) -> BearerToken | None:
        userpass = self.authenticator.auth_userpass(auth_request.userpass)
        if userpass:
            return self.authenticator.auth_request_token(auth_request)
        return None

    ######################################

    def resource_get(self, request: ResourceRequest) -> ResourceResponse:
        def read_file(path: Path):
            if path.is_dir():
                return self.dir_index(path)
            size = os.stat(str(path)).st_size
            logging.info("resource_get: %s", f"{request.action} {size} bytes <= {path}")
            with open(path, "rb") as io:
                return 200, file_headers(path), io.read()

        return self.resource_request(request, read_file)

    def resource_head(self, request: ResourceRequest) -> ResourceResponse:
        def head_file(path: Path):
            return 200, file_headers(path), b""

        return self.resource_request(request, head_file)

    def resource_put(self, request: ResourceRequest) -> ResourceResponse:
        def put_file(path: Path):
            logging.info(
                "resource_put: %s",
                f"{request.action} {len(request.body)} bytes => {path}",
            )
            with open(str(path), "wb") as io:
                io.write(request.body)
            return (
                201,
                {"Content-Type": "text/plain"},
                f"OK : {len(request.body)} bytes".encode(),
            )

        return self.resource_request(request, put_file, must_exist=False)

    ######################################

    def resource_request(
        self,
        request: ResourceRequest,
        with_path: Callable[[Path], ResourceResponse],
        must_exist: bool = True,
    ) -> ResourceResponse:
        path = Path(str(self.resource_root) + normalize_path(request.resource))
        exists = os.access(str(path), os.R_OK)
        logging.info("resource_request: %s", f"{request.action} {path=} {exists=}")
        if must_exist and not exists:
            return status_result(404)
        status, _, body = self.check_access(request)
        logging.info("resource_request:::\n%s", body.decode())
        if status == 200:
            return with_path(path)
        return status_result(401)

    ######################################

    def is_allowed(self, action: str, resource: str, username: str) -> Tuple[bool, Any]:
        rule: Rule = self.solve(action, resource, username)
        result = {
            "permission": rule.permission.name,
            "action": action,
            "resource": resource,
            "user": username,
            "role": rule.role.name,
        }
        return rule.permission.name == "allow", result

    ######################################

    def check_access(self, request: ResourceRequest) -> ResourceResponse:
        username = self.authenticate(request.auth_request)
        success, info = self.is_allowed(request.action, request.resource, username)
        status = 200 if success else 401
        return (
            status,
            {"Content-Type": "application/json"},
            json.dumps(info, indent=2).encode(),
        )

    def authenticate(self, auth_request: AuthRequest) -> str:
        logging.debug("%s", f"authenticate: {auth_request=}")
        userpass = self.authenticator.authenticate(
            None, auth_request.header, auth_request.cookie
        )
        logging.info("%s", f"authenticate: {userpass and userpass.username=}")
        if userpass:
            return userpass.username
        return ""

    def solve(self, action_name: str, resource_path: str, username: str) -> Rule:
        resource_path = normalize_path(resource_path)
        resource = Resource(resource_path)
        domain = self.make_domain(resource)
        solver = Solver(domain=domain)
        user = domain.user_for_name(username)
        request = Request(
            action=Action(action_name),
            resource=resource,
            user=user,
        )

        rules: Iterable = []
        if action_name and username and user:
            rules = solver.find_rules(request)

        if self.verbose:
            logging.info("  action        : %s", repr(request.action.name))
            logging.info("  resource      : %s", repr(request.resource.name))
            logging.info(
                "  user          : %s", repr(request.user and request.user.name)
            )
            logging.info(
                "  groups        : %s",
                repr(request.user and [g.name for g in request.user.groups]),
            )
            logging.info(
                "  roles         : %s",
                repr(
                    request.user
                    and [r.name for r in domain.roles_for_user(request.user)]
                ),
            )
            logging.info("  rules         : %s", len(list(rules)))
            for rule in rules:
                logging.info("                : %s", rule.brief())

        if rules:
            return next(iter(rules))
        return self.default_rule(request)

    ##########################################################

    def default_rule(self, request: Request) -> Rule:
        return Rule(
            permission=Permission("deny"),
            action=request.action,
            role=Role("*"),
            resource=request.resource,
            description="<<DEFAULT>>",
        )

    def make_authenticator(self):
        self.subject_domain, self.password_domain = self.make_auth_domains()
        authenticator = Authenticator(
            subject_domain=self.subject_domain,
            password_domain=self.password_domain,
            cipher_key=self.cipher_key,
            cookie_name=self.auth_cookie_name,
        )
        return authenticator

    ##########################################################
    # This can be overridden to use a different domain loader.

    def make_auth_domains(self):
        root = self.domain_root
        loader = DomainFileLoader()
        subject_domain = loader.load_user_file(root / "user.txt")
        password_domain = loader.load_password_file(root / "password.txt")
        return subject_domain, password_domain

    def make_domain(self, resource: Resource) -> Domain:
        root = self.domain_root
        loader = DomainFileLoader()
        domain = Domain(
            subject_domain=self.subject_domain,
            role_domain=loader.load_membership_file(root / "role.txt"),
            rule_domain=loader.load_rules_for_resource(
                self.resource_root, Path(resource.name)
            ),
            password_domain=self.password_domain,
        )
        return domain

    def dir_index(self, path: Path) -> ResourceResponse:
        files = sorted(os.listdir(str(path)))
        files = [f for f in files if not f.startswith(".")]

        def row(f):
            stat = os.stat(path / f)
            mtime = (
                datetime.fromtimestamp(stat.st_mtime)
                .replace(tzinfo=timezone.utc)
                .isoformat()
            )
            return [f, stat.st_size, mtime]

        rows = [row(f) for f in files]
        tabulate.PRESERVE_WHITESPACE = True
        table = tabulate.tabulate(
            rows, headers=["name", "size", "mtime"], tablefmt="pipe"
        )
        return 200, {"Content-Type": "text/plain"}, (table + "\n").encode()


def normalize_path(path: str) -> str:
    path = re.sub(r"//+", "/", f"/{path}")
    logging.info("%s", f"{path=}")
    return path


def status_result(status: int) -> ResourceResponse:
    return status, {"Content-Type": "text/plain"}, f"{status}\n".encode()


def file_headers(path: Path) -> dict:
    if stat := os.stat(str(path)):
        etag = f"{stat.st_dev}-{stat.st_ino}-{stat.st_size}-{stat.st_mtime}"
        return {
            "Content-Length": str(stat.st_size),
            "Content-Type": "application/binary",
            "ETag": etag,
            # "Last-Modified":
        }
    return {}
