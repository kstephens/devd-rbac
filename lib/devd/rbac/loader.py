from typing import Any, Callable, Iterable, List, Type, IO
from dataclasses import dataclass, field
from pathlib import Path
import re
import logging
from .subject import User, Users, Group
from .credential import UserPass, UserPasses
from .rbac import (
    Resource,
    Action,
    Rule,
    Rules,
    Permission,
    Role,
    Membership,
    Memberships,
    Matcher,
    match_true,
    regex_matcher,
    negate_matcher,
)
from .domain import SubjectDomain, RoleDomain, RuleDomain, PasswordDomain
from .util import getter, mapcat, clean_path, glob_to_regex


@dataclass
class TextLoader:
    prefix: str = field(default="")

    def read_rules(self, io: IO) -> Rules:
        return parse_lines(io, RULE_RX, self.parse_rule_line)

    def parse_rule_line(self, m: re.Match) -> Rules:
        result: List[Rule] = []
        permission = Permission(m["permission"])
        for action in parse_list(m["action"]):
            for role in parse_list(m["role"]):
                for resource in parse_list(m["resource"]):
                    resource_path = clean_path(f"{self.prefix}{resource}")
                    rule = Rule(
                        permission=permission,
                        action=self.parse_pattern(Action, action, True),
                        role=self.parse_pattern(Role, role, True),
                        resource=self.parse_pattern(Resource, resource_path, False),
                    )
                    logging.debug(
                        "  rule: %s",
                        f"{rule.permission.name} {rule.action.name} "
                        f"{rule.role.name} {rule.resource.name} "
                        f"  # {(rule.resource.regex and rule.resource.regex.pattern)!r}",
                    )
                    result.append(rule)
        return result

    def parse_pattern(
        self, constructor: Type, pattern: str, star_always_matches: bool
    ) -> Any:
        if negate := pattern.startswith("!"):
            pattern = pattern.removeprefix("!")
        matcher: Matcher = match_true
        if pattern == "*" and star_always_matches:
            regex = None
            description = pattern
        else:
            regex = glob_to_regex(pattern)
            # pylint: disable-next=unnecessary-lambda-assignment
            matcher = regex_matcher(regex)
            description = regex.pattern
        if negate:
            matcher = negate_matcher(matcher)
            description = f"!{description}"
        obj = constructor(name=pattern, description=pattern, matcher=matcher)
        obj.regex = regex
        return obj

    ##############################

    def read_users(self, io: IO) -> Users:
        return parse_lines(io, USER_RX, self.parse_user_line)

    def parse_user_line(self, m: re.Match) -> Users:
        groups = [Group(group, group) for group in parse_list(m["groups"])]

        def make_user(name):
            return User(name, f"@{name}", groups=groups.copy())

        return [make_user(name) for name in parse_list(m["user"])]

    ##############################

    def read_memberships(self, io: IO) -> Memberships:
        return parse_lines(io, MEMBERSHIP_RX, self.parse_membership_line)

    def parse_membership_line(self, m: re.Match) -> Memberships:
        role = Role(m["role"])
        return [
            self.make_membership(role, member) for member in parse_list(m["members"])
        ]

    def make_membership(self, role: Role, description: str) -> Membership:
        if description.startswith("@"):
            name = description.removeprefix("@")
            return Membership(role=role, member=User(name, description))
        return Membership(role=role, member=Group(description, description))

    ##############################

    def read_passwords(self, io: IO) -> UserPasses:
        def make_password(m: re.Match):
            return [UserPass(**m.groupdict())]

        return parse_lines(io, PASSWORD_RX, make_password)


RULE_RX = re.compile(
    r"rule\s+(?P<permission>\S+)\s+(?P<action>\S+)\s+(?P<role>\S+)\s+(?P<resource>\S+)"
)
MEMBERSHIP_RX = re.compile(r"member\s+(?P<role>\S+)\s+(?P<members>\S+)")
USER_RX = re.compile(r"user\s+(?P<user>\S+)\s+(?P<groups>\S+)")
PASSWORD_RX = re.compile(r"password\s+(?P<username>\S+)\s+(?P<password>\S+)")


def real_open_file(file: Path) -> IO | None:
    try:
        return open(str(file), "r", encoding="utf-8")
    except OSError:
        return None


@dataclass
class DomainFileLoader:
    """
    Loads user/group file, role/membership file, rules for a resource path.
    Creates a static Domain.
    """

    def load_user_file(self, user_file: Path) -> SubjectDomain:
        with open(user_file, encoding="utf-8") as io:
            users = TextLoader().read_users(io)
        group_by_name = {}
        for user in users:
            for group in user.groups:
                group_by_name[group.name] = group
        groups = sorted(group_by_name.values(), key=getter("name"))
        return SubjectDomain(users=users, groups=groups)

    def load_membership_file(self, memberships_file: Path) -> RoleDomain:
        with open(memberships_file, encoding="utf-8") as io:
            memberships = TextLoader().read_memberships(io)
        role_by_name = {}
        for member in memberships:
            role_by_name[member.role.name] = member.role
        roles = sorted(role_by_name.values(), key=getter("name"))
        return RoleDomain(memberships=memberships, roles=roles)

    def load_rules_for_resource(
        self, resource_root: Path, resource_path: Path
    ) -> RuleDomain:
        loader = FileSystemLoader(resource_root=resource_root)
        rules = loader.load_rules(resource_path)
        return RuleDomain(rules=rules)

    def load_password_file(self, password_file: Path) -> PasswordDomain:
        with open(password_file, encoding="utf-8") as io:
            passwords = TextLoader().read_passwords(io)
        return PasswordDomain(passwords=passwords)


@dataclass
class FileSystemLoader:
    resource_root: Path
    open_file: Callable = field(default=real_open_file)
    auth_file_name: str = field(default=".rbac.txt")

    def load_rules(self, resource: Path) -> Rules:
        return mapcat(self.load_auth_file, self.resource_paths(resource))

    def load_auth_file(self, path: Path) -> Rules:
        auth_file = self.auth_file(path)
        io: IO = self.open_file(auth_file)
        if io:
            try:
                return TextLoader(prefix=str(path) + "/").read_rules(io)
            finally:
                io.close()
        return []

    def resource_paths(self, resource: Path) -> Iterable[Path]:
        return list(resource.parents)

    def auth_file(self, path: Path) -> Path:
        return self.resource_root / path.relative_to("/") / self.auth_file_name


###################################


def parse_lines(
    io: IO, rx: re.Pattern, parse: Callable[[re.Match], Any]
) -> Iterable[Any]:
    result: List[Any] = []
    while line := io.readline():
        if m := rx.match(trim_line(line)):
            result.extend(parse(m))
    return result


def parse_list(val: str) -> Iterable[str]:
    return re.split(PARSE_LIST_RX, val)


PARSE_LIST_RX = re.compile(r"\s*,\s*")


def trim_line(line: str) -> str:
    line = line.removesuffix("\n")
    line = re.sub(TRIM_SPACE_RX, "", line)
    return re.sub(COMMENT_RX, "", line)


COMMENT_RX = re.compile(r"#.*$")
TRIM_SPACE_RX = re.compile(r"^\s+|\s+$")
