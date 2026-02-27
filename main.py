"""DeutschLerner — single entry point.

Usage:
    python main.py serve          # Start API server (+ heartbeat if enabled)
    python main.py cli            # Start interactive CLI
    python main.py heartbeat      # Run one heartbeat cycle and exit
    python main.py migrate        # Run database migrations
    python main.py export         # Export all data to JSON
    python main.py import <file>  # Import data from JSON
"""

import asyncio
import json
import logging
import sys

import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def main() -> None:
    """DeutschLerner — German language learning assistant (Chinese → German)."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, type=int, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the API server (+ heartbeat if enabled in config)."""
    import uvicorn

    uvicorn.run(
        "src.api.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )


@main.command()
@click.option("--provider", default="claude", help="AI provider to use")
@click.option("--db-path", default="data/deutsch_lerner.db", help="Database path")
def cli(provider: str, db_path: str) -> None:
    """Start the interactive CLI learning session."""
    from src.cli.interactive import run_interactive

    asyncio.run(run_interactive(provider_name=provider, db_path=db_path))


@main.command()
@click.option("--db-path", default="data/deutsch_lerner.db", help="Database path")
def heartbeat(db_path: str) -> None:
    """Run one heartbeat cycle and exit."""
    import yaml

    from src.api.dependencies import load_config, init_provider_from_config
    from src.heartbeat.scheduler import HeartbeatScheduler
    from src.storage.database import get_engine
    from src.storage.migrations import run_migrations

    async def _run() -> None:
        config = load_config()
        engine = get_engine(db_path)
        await run_migrations(engine)
        init_provider_from_config()

        hb_config = config.get("heartbeat", {})
        scheduler = HeartbeatScheduler(config=hb_config, db_path=db_path)
        result = await scheduler.trigger_now()
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))

    asyncio.run(_run())


@main.command()
@click.option("--db-path", default="data/deutsch_lerner.db", help="Database path")
def migrate(db_path: str) -> None:
    """Run database migrations."""
    from src.storage.database import get_engine
    from src.storage.migrations import run_migrations

    async def _run() -> None:
        engine = get_engine(db_path)
        await run_migrations(engine)
        click.echo("Migrations complete.")

    asyncio.run(_run())


@main.command("export")
@click.option("--db-path", default="data/deutsch_lerner.db", help="Database path")
@click.option("--output", "-o", default="data/export.json", help="Output file")
def export_data(db_path: str, output: str) -> None:
    """Export all learning data to JSON."""
    from src.storage.database import get_engine, get_session
    from src.storage.migrations import run_migrations
    from src.storage.repository import Repository

    async def _run() -> None:
        engine = get_engine(db_path)
        await run_migrations(engine)
        session = await get_session(db_path)
        repo = Repository(session)
        data = await repo.export_all()
        await session.close()

        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        click.echo(f"Data exported to {output}")

    asyncio.run(_run())


@main.command("import")
@click.argument("file", type=click.Path(exists=True))
@click.option("--db-path", default="data/deutsch_lerner.db", help="Database path")
def import_data(file: str, db_path: str) -> None:
    """Import learning data from a JSON file."""
    from src.core.memory import MemoryManager
    from src.storage.database import get_engine, get_session
    from src.storage.migrations import run_migrations
    from src.storage.repository import Repository

    async def _run() -> None:
        engine = get_engine(db_path)
        await run_migrations(engine)
        session = await get_session(db_path)
        repo = Repository(session)
        memory = MemoryManager(repo)

        with open(file, encoding="utf-8") as f:
            data = json.load(f)

        counts = await memory.import_data(data)
        await session.close()
        click.echo(f"Imported: {counts}")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
