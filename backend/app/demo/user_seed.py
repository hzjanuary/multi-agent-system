"""Local-demo role and user seeding helpers.

The functions in this module are explicit operational helpers. They do not run
on application startup, expose APIs, seed workflows, or own transactions.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import hash_password, password_needs_rehash, verify_password
from app.auth.rbac import RoleName
from app.demo.contracts import (
    DEMO_SEED_CONTRACT,
    DemoCredential,
    DemoRoleDefinition,
    DemoSeedContract,
    DemoUserDefinition,
)
from app.models import Role, User


class DemoUserSeedResult(BaseModel):
    """Bounded summary for local demo role/user seed execution."""

    model_config = ConfigDict(frozen=True)

    roles_created: int = 0
    roles_reused: int = 0
    users_created: int = 0
    users_reused: int = 0
    users_updated: int = 0
    passwords_hashed: int = 0
    passwords_refreshed: int = 0
    role_assignments_created: int = 0
    demo_user_emails: tuple[str, ...] = Field(default_factory=tuple)
    role_names: tuple[RoleName, ...] = Field(default_factory=tuple)


async def seed_demo_roles_and_users(
    session: AsyncSession,
    *,
    contract: DemoSeedContract = DEMO_SEED_CONTRACT,
) -> DemoUserSeedResult:
    """Seed local-demo roles and users idempotently.

    The caller owns the session and transaction boundary. This function flushes
    changes so generated primary keys and relationships are available, but it
    never commits.
    """
    credentials_by_key = _credentials_by_key(contract.credentials)
    role_by_name: dict[RoleName, Role] = {}
    roles_created = 0
    roles_reused = 0
    users_created = 0
    users_reused = 0
    users_updated = 0
    passwords_hashed = 0
    passwords_refreshed = 0
    role_assignments_created = 0

    for role_definition in contract.roles:
        role = await _get_role(session, role_definition.role_name)
        if role is None:
            role = _build_role(role_definition)
            session.add(role)
            roles_created += 1
        else:
            roles_reused += 1
        role_by_name[role_definition.role_name] = role

    await session.flush()

    for user_definition in contract.users:
        _validate_demo_user_definition(user_definition)
        credential = credentials_by_key[user_definition.credential_key]
        expected_role = role_by_name[user_definition.role_name]
        user = await _get_user_with_roles(session, user_definition.email)

        if user is None:
            user = _build_user(user_definition, credential)
            session.add(user)
            users_created += 1
            passwords_hashed += 1
        else:
            users_reused += 1
            updated, password_refreshed = _refresh_existing_demo_user(
                user,
                user_definition,
                credential,
            )
            if updated:
                users_updated += 1
            if password_refreshed:
                passwords_refreshed += 1

        if expected_role not in user.roles:
            user.roles.append(expected_role)
            role_assignments_created += 1

    await session.flush()

    return DemoUserSeedResult(
        roles_created=roles_created,
        roles_reused=roles_reused,
        users_created=users_created,
        users_reused=users_reused,
        users_updated=users_updated,
        passwords_hashed=passwords_hashed,
        passwords_refreshed=passwords_refreshed,
        role_assignments_created=role_assignments_created,
        demo_user_emails=tuple(user.email for user in contract.users),
        role_names=tuple(role.role_name for role in contract.roles),
    )


async def _get_role(session: AsyncSession, role_name: RoleName) -> Role | None:
    statement = select(Role).where(Role.name == role_name.value)
    result = await session.scalars(statement)
    return result.one_or_none()


async def _get_user_with_roles(session: AsyncSession, email: str) -> User | None:
    statement = (
        select(User).options(selectinload(User.roles)).where(User.email == email)
    )
    result = await session.scalars(statement)
    return result.one_or_none()


def _build_role(role_definition: DemoRoleDefinition) -> Role:
    return Role(
        name=role_definition.role_name.value,
        description=role_definition.description,
    )


def _build_user(
    user_definition: DemoUserDefinition,
    credential: DemoCredential,
) -> User:
    return User(
        email=user_definition.email,
        hashed_password=hash_password(credential.password),
        full_name=user_definition.full_name,
        is_active=True,
        is_superuser=False,
        roles=[],
    )


def _refresh_existing_demo_user(
    user: User,
    user_definition: DemoUserDefinition,
    credential: DemoCredential,
) -> tuple[bool, bool]:
    updated = False
    password_refreshed = False

    if user.full_name != user_definition.full_name:
        user.full_name = user_definition.full_name
        updated = True
    if not user.is_active:
        user.is_active = True
        updated = True
    if user.is_superuser:
        user.is_superuser = False
        updated = True
    if not verify_password(
        credential.password,
        user.hashed_password,
    ) or password_needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(credential.password)
        updated = True
        password_refreshed = True

    return updated, password_refreshed


def _credentials_by_key(
    credentials: Sequence[DemoCredential],
) -> dict[str, DemoCredential]:
    return {credential.key: credential for credential in credentials}


def _validate_demo_user_definition(user_definition: DemoUserDefinition) -> None:
    if not user_definition.is_demo_only or not user_definition.email.endswith(
        "@example.test",
    ):
        raise ValueError("demo user seeding only supports local-demo users")


__all__ = ["DemoUserSeedResult", "seed_demo_roles_and_users"]
