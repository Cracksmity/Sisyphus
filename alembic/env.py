from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (DATABASE_URL, etc.)
load_dotenv()

# Alembic Config object
config = context.config

# Inyectar DATABASE_URL desde .env; con fallback a SQLite local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sysiphus.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Configurar logging desde el .ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importar los modelos para que autogenerate los detecte
from app.database import Base  # noqa: E402
import app.models  # noqa: E402, F401  — importar para registrar todos los modelos en Base.metadata

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Migraciones en modo offline (sin conexión activa al motor)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite no soporta ALTER TABLE drop column; render_as_batch lo maneja
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migraciones en modo online (motor conectado)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # render_as_batch es necesario para SQLite (no soporta ALTER TABLE nativo)
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
