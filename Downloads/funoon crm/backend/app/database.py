from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# SQLite needs aiosqlite; Postgres needs asyncpg
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    connect_args=connect_args,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def create_tables() -> None:
    """Create all tables and apply any missing column migrations for SQLite."""
    import app.models.client  # noqa: F401
    import app.models.financial  # noqa: F401
    import app.models.library  # noqa: F401
    import app.models.monitoring  # noqa: F401
    import app.models.project  # noqa: F401
    import app.models.settings  # noqa: F401
    import app.models.workspace  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS —
    # run each migration safely and ignore "duplicate column" errors.
    from app.config import settings as _cfg
    if _cfg.database_url.startswith("sqlite"):
        from sqlalchemy import text
        migrations = [
            "ALTER TABLE company_settings ADD COLUMN letterhead_path TEXT",
            "ALTER TABLE billing_records ADD COLUMN notes TEXT",
            "ALTER TABLE invoices ADD COLUMN paid_date TEXT",
            "ALTER TABLE invoices ADD COLUMN doc_type TEXT DEFAULT 'invoice'",
            "ALTER TABLE company_settings ADD COLUMN signature_path TEXT",
            "ALTER TABLE company_settings ADD COLUMN stamp_path TEXT",
        ]
        async with engine.begin() as conn:
            for sql in migrations:
                try:
                    await conn.execute(text(sql))
                except Exception:
                    pass  # column already exists
