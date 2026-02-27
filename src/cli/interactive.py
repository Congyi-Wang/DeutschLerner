"""Rich-based interactive CLI for learning sessions."""

import asyncio
import json
import logging
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from src.ai.factory import create_provider, list_providers
from src.core.engine import LearningEngine
from src.core.marker import Marker
from src.core.memory import MemoryManager
from src.storage.database import get_engine, get_session, close_engine
from src.storage.migrations import run_migrations
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

console = Console()

HELP_TEXT = """
[bold]Available commands:[/bold]
  /topic <text>      — Generate a topic about <text>
  /review            — Review unknown/learning vocabulary
  /mark <id> <status> — Mark vocabulary #id (known/unknown/learning)
  /marks <id> <status> — Mark sentence #id (known/unknown/learning)
  /stats             — Show learning statistics
  /vocab [status]    — List vocabulary (optional: known/unknown/learning)
  /export            — Export memory to JSON
  /provider <name>   — Switch AI provider
  /providers         — List available providers
  /help              — Show this help
  /quit              — Exit
"""


async def run_interactive(provider_name: str = "claude", db_path: str = "data/deutsch_lerner.db") -> None:
    """Run the interactive CLI learning session."""
    # Initialize
    engine_ref = get_engine(db_path)
    await run_migrations(engine_ref)

    current_provider_name = provider_name

    console.print(Panel(
        "[bold blue]DeutschLerner[/bold blue] — 德语学习助手\n"
        f"AI Provider: [green]{current_provider_name}[/green]\n"
        "Type [bold]/help[/bold] for commands, or type a topic to learn.",
        title="Welcome / 欢迎",
    ))

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]🇩🇪 DeutschLerner[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Auf Wiedersehen! 再见！[/yellow]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Get fresh session for each command
        session = await get_session(db_path)
        repo = Repository(session)
        memory = MemoryManager(repo)
        marker = Marker(repo)

        try:
            if user_input == "/quit":
                console.print("[yellow]Auf Wiedersehen! 再见！[/yellow]")
                break

            elif user_input == "/help":
                console.print(HELP_TEXT)

            elif user_input.startswith("/topic "):
                topic_text = user_input[7:].strip()
                if not topic_text:
                    console.print("[red]Please provide a topic.[/red]")
                    continue

                console.print(f"[dim]Generating topic about: {topic_text}...[/dim]")
                provider = create_provider(current_provider_name)
                engine = LearningEngine(provider, memory, marker, repo)
                result = await engine.learn_topic(topic_text)

                _display_topic(result)

            elif user_input == "/review":
                provider = create_provider(current_provider_name)
                engine = LearningEngine(provider, memory, marker, repo)
                items = await engine.review_vocabulary(10)
                if not items:
                    console.print("[yellow]No vocabulary to review yet. Generate some topics first![/yellow]")
                else:
                    _display_review(items)

            elif user_input.startswith("/mark "):
                parts = user_input.split()
                if len(parts) != 3:
                    console.print("[red]Usage: /mark <id> <known|unknown|learning>[/red]")
                    continue
                try:
                    item_id = int(parts[1])
                except ValueError:
                    console.print("[red]ID must be a number.[/red]")
                    continue
                success = await marker.mark_vocabulary(item_id, parts[2])
                if success:
                    await repo.commit()
                    console.print(f"[green]Vocabulary #{item_id} marked as {parts[2]}[/green]")
                else:
                    console.print(f"[red]Vocabulary #{item_id} not found[/red]")

            elif user_input.startswith("/marks "):
                parts = user_input.split()
                if len(parts) != 3:
                    console.print("[red]Usage: /marks <id> <known|unknown|learning>[/red]")
                    continue
                try:
                    item_id = int(parts[1])
                except ValueError:
                    console.print("[red]ID must be a number.[/red]")
                    continue
                success = await marker.mark_sentence(item_id, parts[2])
                if success:
                    await repo.commit()
                    console.print(f"[green]Sentence #{item_id} marked as {parts[2]}[/green]")
                else:
                    console.print(f"[red]Sentence #{item_id} not found[/red]")

            elif user_input == "/stats":
                stats = await memory.get_stats()
                _display_stats(stats)

            elif user_input.startswith("/vocab"):
                parts = user_input.split()
                status = parts[1] if len(parts) > 1 else None
                items = await repo.list_vocabulary(status=status, limit=50)
                _display_vocab_list(items)

            elif user_input == "/export":
                data = await memory.export_data()
                filename = "data/export.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                console.print(f"[green]Data exported to {filename}[/green]")

            elif user_input.startswith("/provider "):
                name = user_input[10:].strip()
                try:
                    create_provider(name)
                    current_provider_name = name
                    console.print(f"[green]Switched to provider: {name}[/green]")
                except (ValueError, RuntimeError) as e:
                    console.print(f"[red]{e}[/red]")

            elif user_input == "/providers":
                providers = list_providers()
                table = Table(title="Available AI Providers")
                table.add_column("Name")
                table.add_column("Env Var")
                table.add_column("Configured")
                for p in providers:
                    table.add_row(p["name"], p["env_var"], p["configured"])
                console.print(table)

            else:
                # Treat any other input as a topic request
                console.print(f"[dim]Generating topic about: {user_input}...[/dim]")
                provider = create_provider(current_provider_name)
                engine = LearningEngine(provider, memory, marker, repo)
                result = await engine.learn_topic(user_input)
                _display_topic(result)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.exception("CLI error")
            await repo.rollback()
        finally:
            await session.close()

    await close_engine()


def _display_topic(result) -> None:
    """Display a learning result in the terminal."""
    topic = result.topic

    console.print(Panel(
        f"[bold]{topic.topic_title_de}[/bold] — {topic.topic_title_cn}",
        title="📚 Topic",
    ))

    if topic.summary_cn:
        console.print(f"\n[italic]{topic.summary_cn}[/italic]\n")

    # Vocabulary table
    if topic.vocabulary:
        table = Table(title="📖 核心词汇 (Core Vocabulary)")
        table.add_column("#", style="dim")
        table.add_column("German", style="bold")
        table.add_column("Gender")
        table.add_column("Chinese")
        table.add_column("Example")

        for i, v in enumerate(topic.vocabulary, 1):
            table.add_row(
                str(i),
                v.get("german", ""),
                v.get("gender", ""),
                v.get("chinese", ""),
                v.get("example_de", ""),
            )
        console.print(table)

    # Sentences
    if topic.sentences:
        console.print("\n[bold]✍️ 重点句型 (Key Sentences)[/bold]")
        for s in topic.sentences:
            console.print(f"  [bold]{s.get('german', '')}[/bold]")
            console.print(f"  {s.get('chinese', '')}")
            if s.get("grammar_note"):
                console.print(f"  [dim]💡 {s['grammar_note']}[/dim]")
            console.print()

    # Grammar tips
    if topic.grammar_tips:
        console.print(Panel(topic.grammar_tips, title="📝 语法提示"))

    # Exercise
    if topic.exercise:
        console.print(Panel(topic.exercise, title="🎯 练习"))

    console.print(
        f"[dim]+{result.vocab_added} vocab, +{result.sentences_added} sentences "
        f"({result.duration_seconds}s)[/dim]"
    )


def _display_review(items: list[dict]) -> None:
    """Display vocabulary items for review."""
    table = Table(title="📝 Vocabulary Review")
    table.add_column("ID", style="dim")
    table.add_column("German", style="bold")
    table.add_column("Gender")
    table.add_column("Chinese")
    table.add_column("Status")
    table.add_column("Reviews", justify="right")

    for item in items:
        table.add_row(
            str(item["id"]),
            item["german"],
            item.get("gender") or "",
            item["chinese"],
            item["status"],
            str(item["review_count"]),
        )
    console.print(table)
    console.print("[dim]Use /mark <id> known|learning|unknown to update status[/dim]")


def _display_stats(stats: dict) -> None:
    """Display learning statistics."""
    table = Table(title="📊 Learning Statistics")
    table.add_column("Category")
    table.add_column("Total", justify="right")
    table.add_column("Known", justify="right", style="green")
    table.add_column("Learning", justify="right", style="yellow")
    table.add_column("Unknown", justify="right", style="red")

    for category in ["vocabulary", "sentences"]:
        s = stats[category]
        table.add_row(
            category.capitalize(),
            str(s["total"]),
            str(s["known"]),
            str(s["learning"]),
            str(s["unknown"]),
        )
    console.print(table)


def _display_vocab_list(items) -> None:
    """Display a list of vocabulary items."""
    if not items:
        console.print("[yellow]No vocabulary items found.[/yellow]")
        return

    table = Table(title=f"📖 Vocabulary ({len(items)} items)")
    table.add_column("ID", style="dim")
    table.add_column("German", style="bold")
    table.add_column("Gender")
    table.add_column("Chinese")
    table.add_column("Status")

    for v in items:
        table.add_row(
            str(v.id),
            v.german,
            v.gender or "",
            v.chinese,
            v.status,
        )
    console.print(table)
