"""Abstract repository interfaces using typing.Protocol."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from models.user import UserOut
from models.team import TeamOut, TeamListOut, TeamMemberOut
from models.project import ProjectOut
from models.column import ColumnOut
from models.card import CardOut
from models.category import CategoryOut
from models.typology import TypologyOut
from models.category_typology import CategoryTypologyOut


class UserRepository(Protocol):
    """Protocol for user persistence operations."""

    def get_by_id(self, user_id: int) -> UserOut | None:
        """Retrieve a user by ID."""
        ...

    def get_by_username(self, username: str) -> UserOut | None:
        """Retrieve a user by username."""
        ...

    def get_by_email(self, email: str) -> UserOut | None:
        """Retrieve a user by email."""
        ...

    def get_password_hash(self, username: str) -> str | None:
        """Return the hashed password for a username, or None if not found."""
        ...

    def create(self, *, email: str, username: str, hashed_password: str) -> UserOut:
        """Create a new user with default role."""
        ...

    def exists(self, user_id: int) -> bool:
        """Return True if a user with the given ID exists."""
        ...


class TeamRepository(Protocol):
    """Protocol for team persistence operations."""

    def get(self, team_id: int) -> TeamOut | None:
        """Retrieve a team by ID, including members."""
        ...

    def list_all(self) -> list[TeamListOut]:
        """Return all teams ordered by name."""
        ...

    def list_by_user(self, user_id: int) -> list[TeamListOut]:
        """Return teams the user belongs to."""
        ...

    def create(self, *, name: str, description: str | None, creator_id: int) -> TeamOut:
        """Create a team and add the creator as admin."""
        ...

    def update(self, team_id: int, updates: dict) -> TeamOut | None:
        """Apply partial updates to a team. Return None if not found."""
        ...

    def name_exists(self, name: str) -> bool:
        """Return True if a team with the given name exists."""
        ...

    def get_membership(self, user_id: int, team_id: int) -> TeamMemberOut | None:
        """Return the membership record for a user in a team, or None."""
        ...

    def add_member(self, *, team_id: int, user_id: int, role: str) -> TeamMemberOut:
        """Add a user to a team with the given role."""
        ...

    def update_member_role(self, *, team_id: int, user_id: int, role: str) -> TeamMemberOut | None:
        """Update a member's role. Return None if membership not found."""
        ...

    def remove_member(self, *, team_id: int, user_id: int) -> bool:
        """Remove a member from a team. Return False if not found."""
        ...

    def admin_count(self, team_id: int) -> int:
        """Return the number of admins in a team."""
        ...

    def list_user_team_ids(self, user_id: int) -> list[int]:
        """Return all team IDs that a user belongs to."""
        ...


class ProjectRepository(Protocol):
    """Protocol for project persistence operations."""

    def get(self, project_id: int) -> ProjectOut | None:
        """Retrieve a project by ID."""
        ...

    def list_accessible(self, *, user_id: int, role: str, team_id: int | None = None) -> list[ProjectOut]:
        """List non-archived projects accessible to the user."""
        ...

    def create(self, *, title: str, description: str | None, position: int, team_id: int, owner_id: int) -> ProjectOut:
        """Create a new project."""
        ...

    def update(self, project_id: int, updates: dict) -> ProjectOut | None:
        """Apply partial updates. Return None if not found."""
        ...

    def set_archived(self, project_id: int, archived: bool) -> ProjectOut | None:
        """Archive or unarchive a project. Return None if not found."""
        ...


class ColumnRepository(Protocol):
    """Protocol for board column persistence operations."""

    def get(self, column_id: int) -> ColumnOut | None:
        """Retrieve a column by ID (without cards)."""
        ...

    def list_by_project(self, project_id: int, *, include_hidden: bool = False) -> list[ColumnOut]:
        """List columns for a project, ordered by position. Includes cards."""
        ...

    def create(self, *, title: str, color: str, position: int, project_id: int, owner_id: int | None = None, is_mandatory: bool = False, is_visible_by_default: bool = True) -> ColumnOut:
        """Create a new column."""
        ...

    def update(self, column_id: int, updates: dict) -> ColumnOut | None:
        """Apply partial updates. Return None if not found."""
        ...

    def delete(self, column_id: int) -> bool:
        """Delete a column. Return False if not found."""
        ...

    def ensure_mandatory_columns(self, project_id: int, owner_id: int) -> None:
        """Create mandatory columns for a project if they don't exist yet."""
        ...


class CardRepository(Protocol):
    """Protocol for card persistence operations."""

    def get(self, card_id: int) -> CardOut | None:
        """Retrieve a card by ID."""
        ...

    def get_column_id(self, card_id: int) -> int | None:
        """Return the column_id for a card, or None if not found."""
        ...

    def list_by_due_date(self, *, accessible_project_ids: list[int] | None, owner_id: int | None, overdue: bool = False) -> list[CardOut]:
        """Return cards with due_date set, optionally filtered to overdue only.
        If accessible_project_ids is None, return all (superadmin).
        """
        ...

    def list_by_assignee(self, user_id: int) -> list[CardOut]:
        """Return cards assigned to a user, ordered by position."""
        ...

    def create(self, data: dict) -> CardOut:
        """Create a card from a dict of field values."""
        ...

    def update(self, card_id: int, updates: dict) -> CardOut | None:
        """Apply partial updates. Return None if not found."""
        ...

    def delete(self, card_id: int) -> bool:
        """Delete a card. Return False if not found."""
        ...


class CategoryRepository(Protocol):
    """Protocol for category persistence operations."""

    def get(self, category_id: int) -> CategoryOut | None:
        """Retrieve a category by ID."""
        ...

    def list_all(self) -> list[CategoryOut]:
        """Return all categories."""
        ...

    def create(self, *, name: str, description: str | None) -> CategoryOut:
        """Create a new category."""
        ...

    def update(self, category_id: int, updates: dict) -> CategoryOut | None:
        """Apply partial updates. Return None if not found."""
        ...

    def delete(self, category_id: int) -> bool:
        """Delete a category. Return False if not found."""
        ...

    def name_exists(self, name: str) -> bool:
        """Return True if a category with the given name exists."""
        ...

    def exists(self, category_id: int) -> bool:
        """Return True if a category with the given ID exists."""
        ...


class TypologyRepository(Protocol):
    """Protocol for typology persistence operations."""

    def get(self, typology_id: int) -> TypologyOut | None:
        """Retrieve a typology by ID."""
        ...

    def list_all(self) -> list[TypologyOut]:
        """Return all typologies."""
        ...

    def create(self, *, name: str, description: str | None) -> TypologyOut:
        """Create a new typology."""
        ...

    def update(self, typology_id: int, updates: dict) -> TypologyOut | None:
        """Apply partial updates. Return None if not found."""
        ...

    def delete(self, typology_id: int) -> bool:
        """Delete a typology. Return False if not found."""
        ...

    def name_exists(self, name: str) -> bool:
        """Return True if a typology with the given name exists."""
        ...

    def exists(self, typology_id: int) -> bool:
        """Return True if a typology with the given ID exists."""
        ...


class CategoryTypologyRepository(Protocol):
    """Protocol for category-typology mapping operations."""

    def list_all(self) -> list[CategoryTypologyOut]:
        """Return all mappings."""
        ...

    def set_mapping(self, *, category_id: int, typology_id: int, enabled: bool) -> CategoryTypologyOut:
        """Create or update a mapping."""
        ...

    def is_combination_allowed(self, category_id: int, typology_id: int) -> bool:
        """Return True if the combination is enabled."""
        ...
