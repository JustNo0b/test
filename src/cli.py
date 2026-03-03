"""CLI interface for the content assistant."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

import click
from rich.console import Console
from rich.table import Table

from src.config import get_config
from src.monitor.channels import load_channels
from src.monitor.database import Database
from src.monitor.digest import DigestGenerator
from src.monitor.scraper import TelegramScraper

console = Console()


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def cli(verbose: bool) -> None:
    """📡 Контент AI-помощник — мини контент-заводик"""
    setup_logging(verbose)


@cli.command()
@click.option("--date", "target_date", type=click.DateTime(["%Y-%m-%d"]),
              default=None, help="Дата для сбора (по умолчанию — вчера)")
def scrape(target_date: datetime | None) -> None:
    """Собрать посты из ТГ-каналов за указанную дату."""
    asyncio.run(_scrape(target_date))


async def _scrape(target_date: datetime | None) -> None:
    cfg = get_config()
    channels = load_channels(cfg.channels_file)

    if not channels:
        console.print("[yellow]⚠ Список каналов пуст. Добавьте каналы в channels.yml[/yellow]")
        return

    if not cfg.telegram.api_id or not cfg.telegram.api_hash:
        console.print("[red]✗ Не заданы TELEGRAM_API_ID и TELEGRAM_API_HASH в .env[/red]")
        return

    if target_date is None:
        today = date.today()
        date_from = datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        date_to = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    else:
        date_from = target_date.replace(tzinfo=timezone.utc)
        date_to = date_from + timedelta(days=1)

    db = Database(cfg.database_path)
    await db.connect()

    scraper = TelegramScraper(
        cfg.telegram.api_id, cfg.telegram.api_hash, cfg.telegram.session_path
    )
    await scraper.start()

    total = 0
    for ch in channels:
        username = ch["username"] if isinstance(ch, dict) else ch
        try:
            count = await scraper.scrape_channel(username, db, date_from, date_to)
            total += count
            console.print(f"  [green]✓[/green] @{username}: {count} новых постов")
        except Exception as e:
            console.print(f"  [red]✗[/red] @{username}: {e}")

    await scraper.stop()
    await db.close()

    console.print(f"\n[bold green]Итого: {total} новых постов собрано[/bold green]")


@cli.command()
@click.option("--start", "start_date", type=click.DateTime(["%Y-%m-%d"]),
              default=None, help="Начало периода")
@click.option("--end", "end_date", type=click.DateTime(["%Y-%m-%d"]),
              default=None, help="Конец периода")
def digest(start_date: datetime | None, end_date: datetime | None) -> None:
    """Сгенерировать еженедельный HTML-дайджест."""
    asyncio.run(_digest(start_date, end_date))


async def _digest(start_date: datetime | None, end_date: datetime | None) -> None:
    cfg = get_config()
    db = Database(cfg.database_path)
    await db.connect()

    generator = DigestGenerator(cfg.monitor_output_dir)
    path = await generator.generate(
        db,
        week_start=start_date.date() if start_date else None,
        week_end=end_date.date() if end_date else None,
    )

    await db.close()
    console.print(f"[bold green]Дайджест сохранён: {path}[/bold green]")


@cli.command()
def status() -> None:
    """Показать текущий статус: каналы, посты, дайджесты."""
    asyncio.run(_status())


async def _status() -> None:
    cfg = get_config()

    channels = load_channels(cfg.channels_file)
    console.print(f"\n[bold]📡 Каналов в списке:[/bold] {len(channels)}")
    for ch in channels:
        name = ch["username"] if isinstance(ch, dict) else ch
        tags = ch.get("tags", []) if isinstance(ch, dict) else []
        console.print(f"  • @{name} {tags}")

    db = Database(cfg.database_path)
    await db.connect()

    cursor = await db.conn.execute("SELECT COUNT(*) FROM posts")
    total_posts = (await cursor.fetchone())[0]

    cursor = await db.conn.execute("SELECT COUNT(*) FROM digests")
    digest_count = (await cursor.fetchone())[0]

    await db.close()

    table = Table(title="📊 Статистика")
    table.add_column("Метрика", style="cyan")
    table.add_column("Значение", style="green")

    table.add_row("Всего постов", str(total_posts))
    table.add_row("Дайджестов", str(digest_count))

    console.print(table)


@cli.command()
def pipeline() -> None:
    """Полный пайплайн: скрапинг → дайджест (еженедельно)."""
    asyncio.run(_pipeline())


async def _pipeline() -> None:
    cfg = get_config()
    channels = load_channels(cfg.channels_file)

    if not channels:
        console.print("[yellow]⚠ Список каналов пуст. Добавьте каналы в channels.yml[/yellow]")
        return

    console.print("[bold]🔄 Запуск полного пайплайна...[/bold]\n")

    console.print("[bold cyan]1/2 Скрапинг постов за вчера[/bold cyan]")
    await _scrape(None)

    today = date.today()
    if today.weekday() == 0:
        console.print("\n[bold cyan]2/2 Генерация еженедельного дайджеста[/bold cyan]")
        await _digest(None, None)
    else:
        console.print(
            f"\n[dim]2/2 Дайджест генерируется по понедельникам "
            f"(сегодня — {today.strftime('%A')})[/dim]"
        )

    console.print("\n[bold green]✓ Пайплайн завершён[/bold green]")


if __name__ == "__main__":
    cli()
