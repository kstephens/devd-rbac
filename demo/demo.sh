#!/usr/bin/env bash
set -x

: Denied: no credentials:
curl http://localhost:8888/__/access/GET/a/f1.txt
curl http://bob@localhost:8888/__/access/GET/a/f1.txt
curl http://bob:@localhost:8888/__/access/GET/a/f1.txt

: Allowed: basic auth credentials:
curl http://bob:b0b3r7@localhost:8888/__/access/GET/a/f1.txt
curl http://bob:b0b3r7@localhost:8888/a/f1.txt

: Accessible, but does not exist:
curl http://bob:b0b3r7@localhost:8888/__/access/GET/a/f2.txt
curl http://bob:b0b3r7@localhost:8888/a/f2.txt

: Creating a Bearer Token:
bearer_token="$(curl -X POST -H 'Content-Type: application/json' --data-binary '{"userpass": {"username": "bob", "password": "b0b3r7"}, "description": "for demo", "lifetime": 60}' http://localhost:8888/__/auth_token_request | tee /dev/stderr | jq -r '.token.value')"
H="Authorization: Bearer $bearer_token"
curl -H "$H" http://localhost:8888/a/f1.txt

: PUT content:
curl --data-binary='abc' -X PUT -H "$H" http://localhost:8888/a/f9.txt
curl http://bob:b0b3r7@localhost:8888/a/f9.txt
curl -H "$H" http://localhost:8888/a/f9.txt

curl --data-binary 'abc' -X PUT http://bob:b0b3r7@localhost:8888/a/f9.txt
curl --data-binary 'abc' -X PUT http://bob:b0b3r7@localhost:8888/a/b/bob.txt
curl --data-binary 'frank was here!' -X PUT http://frank:crick@localhost:8888/a/b/frank.txt
