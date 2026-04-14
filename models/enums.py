"""Shared enumerations used across the domain."""

import enum


class RoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    user = "user"


class TeamRoleEnum(str, enum.Enum):
    admin = "admin"
    member = "member"
