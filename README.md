# 📡 Контент AI-помощник

Мини контент-заводик — полный цикл от мониторинга ТГ-каналов до публикации.

## Что делает

- Ежедневно собирает посты из указанных Telegram-каналов
- Генерирует красивый HTML-дайджест за неделю
- Хранит все посты в локальной SQLite-базе

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Заполните .env:
#   TELEGRAM_API_ID, TELEGRAM_API_HASH — с https://my.telegram.org
#   TELEGRAM_PHONE — ваш номер телефона
```

### 3. Добавить каналы

Отредактируйте `channels.yml`:

```yaml
channels:
  - username: durov
    tags: [tech, crypto]
  - username: ai_newz
    tags: [ai]
```

### 4. Использование

```bash
# Проверить статус
python main.py status

# Собрать посты за вчера
python main.py scrape

# Собрать посты за конкретную дату
python main.py scrape --date 2025-03-01

# Сгенерировать еженедельный дайджест
python main.py digest

# Полный пайплайн (скрапинг → дайджест)
python main.py pipeline
```

## Команды CLI

| Команда    | Описание                                |
|------------|-----------------------------------------|
| `status`   | Статистика: каналы, посты, дайджесты    |
| `scrape`   | Сбор постов из ТГ-каналов за дату       |
| `digest`   | Генерация HTML-дайджеста за неделю      |
| `pipeline` | Полный цикл: скрапинг → дайджест       |

## Тестирование

```bash
pytest tests/ -v
```

## Структура проекта

```
├── main.py                 # Точка входа
├── channels.yml            # Список ТГ-каналов
├── requirements.txt        # Зависимости Python
├── .env.example            # Шаблон переменных окружения
├── src/
│   ├── config.py           # Конфигурация
│   ├── cli.py              # CLI-интерфейс
│   └── monitor/
│       ├── scraper.py      # Скрапер ТГ-каналов (Telethon)
│       ├── digest.py       # Генератор HTML-дайджестов (Jinja2)
│       ├── database.py     # SQLite хранилище
│       └── channels.py     # Загрузчик списка каналов
├── skills/                 # Файлы контент-стратегии
│   ├── context.md
│   ├── strategy.md
│   ├── style-profile.md
│   └── sample-posts.md
├── storage/                # Данные (gitignored)
│   └── monitor/            # HTML-дайджесты
└── tests/                  # Тесты
```

## Технологии

- **Python 3.12+**
- **Telethon** — Telegram client для чтения каналов
- **Jinja2** — шаблоны HTML-дайджестов
- **SQLite (aiosqlite)** — локальное хранилище постов
- **Click + Rich** — CLI с красивым выводом
