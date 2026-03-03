# AGENTS.md

## Cursor Cloud specific instructions

Контент AI-помощник на Python 3.12+ — мониторинг ТГ-каналов, классификация рекламы, генерация дайджестов.

### Запуск

- **Установка**: `pip install -r requirements.txt`
- **CLI**: `python3 main.py [command]` — доступные команды описаны в `README.md`
- **Тесты**: `python3 -m pytest tests/ -v`
- **Превью дайджестов**: `python3 -m http.server 8080 --directory storage/monitor`

### Внешние зависимости (требуют секреты)

- **Telegram API** (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`) — для скрапинга каналов. Без них команда `scrape` не работает.
- **OpenAI API** (`OPENAI_API_KEY`) — для классификации рекламы. Без него команда `classify` не работает.
- Команды `status` и `digest` работают без секретов (используют только локальную SQLite-базу).

### Важное

- На системе стоит `python3`, а не `python`. Используйте `python3 main.py ...`.
- БД создаётся автоматически при первом запуске в `storage/content.db`.
- Список каналов задаётся в `channels.yml` (YAML-формат).
