# devd-rbac

## Python RBAC Library

Provides:

* User, Group subjects
* Role, Rule, Permission objects
* User and Group role memberships
* HTTP Basic Auth, Bearer Tokens, Cookies w/ expiry
* Web API for auth checks and static file services
* Basic LDAP support

## Development

```bash
make help
make setup
. venv/bin/activate
. .env
```

## API

```bash
. venv/bin/activate
. .env

# bin/devd --port=8888 --host=0.0.0.0 rbac api run &

python -m devd.rbac.api &

# See API
open http://127.0.0.1:8888/__

# HTTP Login
open http://127.0.0.1:8888/__/login

# Run the demo:
./demo/demo.sh
```
