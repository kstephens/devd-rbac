# devd-rbac

## Python RBAC Library

Provides:

* User, Group subjects
* Role, Rule, Permission objects
* User and Group role memberships
* Basic User Auth, Auth Tokens, Cookies
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
bin/devd --port=8989 --host=0.0.0.0 rbac api run &
open http://127.0.0.1:8989/__
```
