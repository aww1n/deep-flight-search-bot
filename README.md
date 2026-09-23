# ✈️ Deep Flight Search Bot

[![CI](https://github.com/aww1n/deep-flight-search-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/aww1n/deep-flight-search-bot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Telegram-бот для углублённого исследования авиамаршрутов. Он сравнивает обычный билет с
отдельными one-way, self-transfer, вылетами из соседних городов, хабами третьих стран и
альтернативными аэропортами с наземным продолжением.

> Бот — исследовательский помощник, а не билетное агентство. Он не бронирует билеты и не
> гарантирует цену. Финальную стоимость и условия необходимо подтвердить у продавца.

## Возможности

- понимает запрос на русском языке и дозапрашивает критичные параметры;
- ведёт отдельный контекст для каждого Telegram-чата;
- использует OpenAI Responses API с live web search;
- ищет прямые, составные и несимметричные маршруты туда/обратно;
- считает билеты, багаж и обязательные дополнительные расходы, когда они подтверждены;
- показывает риски self-transfer и отличает `VERIFIED`, `PARTIALLY VERIFIED`, `DISCOVERY`;
- сохраняет только идентификатор API-диалога в локальной SQLite;
- разбивает длинные ответы под лимит Telegram;
- запускается локально или в Docker.

## Как это работает

```text
Telegram → Bot API long polling → Deep Flight Search prompt
                                  ↓
                         OpenAI Responses API
                                  ↓
                            live web search
                                  ↓
                     ответ со ссылками и статусами
```

OpenAI web search может находить и открывать публичные страницы, но не является полноценной
автоматизацией динамической формы бронирования. Если цена на нужную дату не видна на открытой
странице, промпт требует показать её как неподтверждённую, а не выдумывать.

## Быстрый запуск

### 1. Получите ключи

1. Создайте бота через [@BotFather](https://t.me/BotFather) и скопируйте Telegram token.
2. Создайте API key в [OpenAI Platform](https://platform.openai.com/api-keys).

Не публикуйте ключи и не добавляйте `.env` в Git.

### 2. Запустите локально

```bash
git clone https://github.com/aww1n/deep-flight-search-bot.git
cd deep-flight-search-bot
cp .env.example .env
```

Заполните `.env`, затем:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
deep-flight-bot
```

### 3. Или запустите в Docker

```bash
cp .env.example .env
# заполните .env
docker compose up --build -d
docker compose logs -f bot
```

## Конфигурация

| Переменная | Обязательна | По умолчанию | Назначение |
|---|---:|---|---|
| `TELEGRAM_BOT_TOKEN` | да | — | токен от BotFather |
| `OPENAI_API_KEY` | да | — | серверный ключ OpenAI API |
| `OPENAI_MODEL` | нет | `gpt-6-sol` | модель с поддержкой web search |
| `OPENAI_REASONING_EFFORT` | нет | `high` | глубина анализа |
| `DATABASE_PATH` | нет | `data/bot.db` | файл контекста SQLite |
| `LOG_LEVEL` | нет | `INFO` | уровень логирования |

Модель `gpt-6-sol` выбрана как баланс качества и стоимости. Для наиболее сложного поиска
можно указать `gpt-6-astra`, а для более дешёвого — `gpt-6-luna`.

## Использование

Напишите боту, например:

```text
Москва → Санья, 10–20 ноября 2026, ±2 дня, 2 взрослых,
гражданство РФ, багаж 23 кг, self-transfer разрешён.
```

Команды:

- `/start` — инструкция и пример;
- `/help` — повторить подсказку;
- `/new` — удалить контекст текущего поиска.

## Разработка

```bash
make install
make check
```

Проект намеренно использует Telegram Bot API напрямую через `httpx`: меньше зависимостей,
прозрачный long polling и простой перенос на webhook в будущем.

```text
src/flight_bot/
├── config.py       # env-конфигурация
├── main.py         # сборка приложения
├── service.py      # OpenAI Responses API + web search
├── store.py        # состояние чатов в SQLite
├── telegram.py     # Telegram Bot API и команды
├── text.py         # безопасное разбиение сообщений
└── system_ru.md    # строгий поисковый промпт
```

## Ограничения

- Цены меняются между поиском и переходом к бронированию.
- Некоторые сайты закрывают динамическую выдачу от поисковых роботов.
- Web search не обходит CAPTCHA, авторизацию и anti-bot-защиту.
- Визовые правила и правила транзита нужно финально подтверждать на официальном ресурсе.
- Один процесс long polling подходит для небольшого/среднего бота; для горизонтального
  масштабирования стоит перейти на webhook и внешнюю БД.

## Безопасность и приватность

- ключи читаются только из переменных окружения;
- `.env` и база исключены из Git;
- в логах не выводятся токены и тексты пользовательских запросов;
- для продолжения диалога Responses API хранит состояние ответа (`store=True`);
- перед публичным запуском добавьте собственную политику конфиденциальности и сроки хранения.

О проблемах безопасности сообщайте по инструкции в [SECURITY.md](SECURITY.md).

## Документация

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API quickstart](https://developers.openai.com/api/docs/quickstart)
- [OpenAI web search](https://developers.openai.com/api/docs/guides/tools-web-search)

## Лицензия

[MIT](LICENSE)
