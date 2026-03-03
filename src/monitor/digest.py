"""Weekly digest generator — produces an HTML digest from stored posts."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Template

if TYPE_CHECKING:
    from src.monitor.database import Database

logger = logging.getLogger(__name__)

DIGEST_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Дайджест {{ week_start }} — {{ week_end }}</title>
<style>
  :root { --bg: #0f0f23; --card: #1a1a36; --accent: #f5c542; --text: #e0e0e0; --muted: #888; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; line-height: 1.6; }
  .header { text-align: center; margin-bottom: 2rem; }
  .header h1 { color: var(--accent); font-size: 1.8rem; }
  .header p { color: var(--muted); margin-top: 0.5rem; }
  .stats { display: flex; gap: 1rem; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap; }
  .stat { background: var(--card); padding: 1rem 1.5rem; border-radius: 12px; text-align: center; }
  .stat .num { font-size: 1.6rem; font-weight: 700; color: var(--accent); }
  .stat .label { font-size: 0.85rem; color: var(--muted); }
  .channel-group { margin-bottom: 2rem; }
  .channel-group h2 { color: var(--accent); font-size: 1.2rem; margin-bottom: 0.8rem; border-bottom: 1px solid #333; padding-bottom: 0.4rem; }
  .post { background: var(--card); border-radius: 12px; padding: 1.2rem; margin-bottom: 0.8rem; }
  .post .meta { font-size: 0.8rem; color: var(--muted); margin-bottom: 0.5rem; }
  .post .text { white-space: pre-wrap; }
  .post .text a { color: var(--accent); }
  .post .engagement { margin-top: 0.6rem; font-size: 0.8rem; color: var(--muted); }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .footer { text-align: center; margin-top: 3rem; color: var(--muted); font-size: 0.8rem; }
</style>
</head>
<body>
<div class="header">
  <h1>📡 Еженедельный дайджест</h1>
  <p>{{ week_start }} — {{ week_end }}</p>
</div>

<div class="stats">
  <div class="stat"><div class="num">{{ total_posts }}</div><div class="label">постов</div></div>
  <div class="stat"><div class="num">{{ channels_count }}</div><div class="label">каналов</div></div>
</div>

{% for channel, posts in grouped_posts.items() %}
<div class="channel-group">
  <h2>@{{ channel }} {% if channel_titles[channel] %}— {{ channel_titles[channel] }}{% endif %}</h2>
  {% for post in posts %}
  <div class="post">
    <div class="meta">
      {{ post.date[:16] }}
      {% if post.url %} · <a href="{{ post.url }}" target="_blank">открыть ↗</a>{% endif %}
    </div>
    <div class="text">{{ post.text[:500] }}{% if post.text|length > 500 %}…{% endif %}</div>
    <div class="engagement">👁 {{ post.views }} · ↗ {{ post.forwards }} · ❤ {{ post.reactions_count }}</div>
  </div>
  {% endfor %}
</div>
{% endfor %}

<div class="footer">
  Сгенерировано контент-помощником · {{ generated_at }}
</div>
</body>
</html>
""")


class DigestGenerator:
    def __init__(self, output_dir: str) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        db: Database,
        week_start: date | None = None,
        week_end: date | None = None,
    ) -> str:
        """Generate a weekly HTML digest. Returns path to the generated file."""
        if week_end is None:
            week_end = date.today()
        if week_start is None:
            week_start = week_end - timedelta(days=7)

        start_str = week_start.isoformat()
        end_str = week_end.isoformat()

        posts = await db.get_posts_for_period(start_str, end_str)

        grouped: dict[str, list] = {}
        channel_titles: dict[str, str] = {}
        for post in posts:
            ch = post["channel_username"]
            if ch not in grouped:
                grouped[ch] = []
                channel_titles[ch] = post["channel_title"] or ""
            grouped[ch].append(
                {
                    "date": post["date"],
                    "text": post["text"] or "",
                    "url": post["url"],
                    "views": post["views"],
                    "forwards": post["forwards"],
                    "reactions_count": post["reactions_count"],
                }
            )

        html = DIGEST_TEMPLATE.render(
            week_start=start_str,
            week_end=end_str,
            total_posts=len(posts),
            channels_count=len(grouped),
            grouped_posts=grouped,
            channel_titles=channel_titles,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        filename = f"digest_{start_str}_{end_str}.html"
        filepath = self._output_dir / filename
        filepath.write_text(html, encoding="utf-8")

        await db.save_digest(start_str, end_str, str(filepath))
        logger.info("Digest saved: %s", filepath)
        return str(filepath)
