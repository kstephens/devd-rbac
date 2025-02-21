from typing import Literal, Annotated, Callable
import re
import logging
import uvicorn
from fastapi import FastAPI, Path, Form, status
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from fastapi.requests import Request
from asgiref.sync import async_to_sync
from .app import App, AuthRequest, ResourceRequest, UserPass, AuthTokenRequest
from ..util import setup_logging

####################################################

app = App(
    resource_root="tests/data/rbac/root",
    domain_root="tests/data/rbac/domain",
)

####################################################

UserName = Annotated[str, Path(pattern=re.compile(r"^[a-z][a-z0-9_]*$"))]
ActionName = Literal["GET", "HEAD", "PUT", "DELETE"]

api = FastAPI(
    docs_url="/__/docs",
    openapi_url="/__/openapi.json",
)


@api.get("/__/")
def redirect_to_docs():
    return RedirectResponse("/__/docs", status_code=status.HTTP_303_SEE_OTHER)


@api.get("/__/login")
def get_login():
    body = """
<html>
<head>
</head>
    <body>
        <form method="post">
            <div>
                <label for="username">Username:</label><br>
                <input type="text" id="username" name="username"><br>
            </div>
            <div>
                <label for="password">Password:</label><br>
                <input type="password" id="password" name="password">
            </div>
            <div>
                <input type="submit" id="submit" />
            </div>
        </form>
    </body>
</html>
    """
    return HTMLResponse(content=body, status_code=200)


@api.post("/__/login")
def post_login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    response: Response,
):
    userpass = UserPass(username, password)
    cookie = app.login(userpass)
    logging.info("post_login %s", f"{cookie=}")
    if cookie:
        response = HTMLResponse(content="OK", status_code=200)
        response.set_cookie(cookie.name, cookie.value)
    else:
        response = RedirectResponse("/__/login", status_code=status.HTTP_303_SEE_OTHER)
    return response


@api.post("/__/auth_token_request")
def post_auth_token(
    request: AuthTokenRequest,
):
    token = app.auth_token(request)
    logging.info("post_auth_token %s", f"{token=}")
    if token:
        return {
            "value": token.value,
            "headers": {
                "Authorization": f"Bearer {token.value}",
            },
        }
    return None


@api.get("/__/logout")
def get_logout():
    response = HTMLResponse(content="OK", status_code=200)
    response.delete_cookie(app.auth_cookie_name)
    return response


@api.get("/__/whoami")
def get_whoami(request: Request):
    username = app.authenticate(auth_request(request))
    return HTMLResponse(content=username, status_code=200)


######################################


@api.get("/__/access/{action}/{resource:path}")
def check_get_access(action: ActionName, resource: str, request: Request):
    return resource_request(action, resource, request, app.check_access)


######################################


@api.get("/{resource:path}")
def get_resource(resource: str, request: Request):
    return resource_request("GET", resource, request, app.resource_get)


@api.head("/{resource:path}")
def head_resource(resource: str, request: Request):
    return resource_request("HEAD", resource, request, app.resource_head)


@api.put("/{resource:path}")
def put_resource(resource: str, request: Request):
    return resource_request(
        "PUT", resource, request, app.resource_put, async_to_sync(request.body)()
    )


def auth_request(request: Request) -> AuthRequest:
    return AuthRequest(
        request.headers.get("Authorization"),
        request.cookies.get(app.auth_cookie_name),
    )


def resource_request(
    action: ActionName,
    resource: str,
    request: Request,
    func: Callable,
    body: bytes = b"",
) -> Response:
    req = ResourceRequest(action, resource, auth_request(request), body)
    code, headers, body = func(req)
    return Response(content=body, headers=headers, status_code=code)


######################################


def main(*_args, **kwargs):
    kwargs = {
        "host": "0.0.0.0",
        "port": 8888,
        "reload": True,
        "reload_dirs": ["lib"],
        "reload_excludes": ["*_test.py", "*.pyi"],
    } | kwargs
    kwargs["port"] = int(kwargs["port"])
    uvicorn.run("devd.rbac.api:api", **kwargs)


if __name__ == "__main__":
    setup_logging(level=logging.INFO, formatter="json")
    main()
