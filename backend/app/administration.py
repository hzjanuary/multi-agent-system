"""Host-authorized explicit account administration; never seeds business data."""

from sqlalchemy import func, select, text

from app.auth.password import hash_password
from app.db import get_session_factory
from app.models import Role, User

ROLES = ("admin", "operator", "viewer")


async def provision(
    email: str, password: str, *, role: str = "admin", bootstrap: bool = False
) -> dict[str, str]:
    if role not in ROLES or "@" not in email or len(email) > 320 or len(password) < 12:
        raise ValueError(
            "invalid_account: valid email, generic role and "
            "password of at least 12 characters required"
        )
    async with get_session_factory()() as session, session.begin():
        # Serialize the first-admin decision even when there are no user rows yet.
        await session.execute(text("SELECT pg_advisory_xact_lock(290001)"))
        count = await session.scalar(select(func.count()).select_from(User))
        if bootstrap and count:
            raise ValueError(
                "bootstrap_refused: installation already contains users; "
                "use explicit administration"
            )
        existing = await session.scalar(select(User).where(User.email == email))
        if existing:
            raise ValueError("user_exists: account unchanged")
        roles = {r.name: r for r in (await session.scalars(select(Role))).all()}
        for name in ROLES:
            if name not in roles:
                roles[name] = Role(name=name)
                session.add(roles[name])
        user = User(
            email=email, hashed_password=hash_password(password), roles=[roles[role]]
        )
        session.add(user)
        await session.flush()
        return {"id": str(user.id), "email": email, "role": role}


async def set_role(email: str, role: str) -> dict[str, str]:
    if role not in ROLES:
        raise ValueError("invalid_role")
    async with get_session_factory()() as session, session.begin():
        await session.execute(text("SELECT pg_advisory_xact_lock(290001)"))
        user = await session.scalar(
            select(User).where(User.email == email).with_for_update()
        )
        target = await session.scalar(select(Role).where(Role.name == role))
        if user is None or target is None:
            raise ValueError("user_or_role_not_found")
        if role != "admin" and any(r.name == "admin" for r in user.roles):
            admins = (
                await session.scalars(
                    select(User)
                    .join(User.roles)
                    .where(Role.name == "admin", User.is_active.is_(True))
                )
            ).all()
            if len(admins) <= 1:
                raise ValueError(
                    "last_administrator: create another administrator first"
                )
        user.roles = [target]
        return {"email": email, "role": role}
